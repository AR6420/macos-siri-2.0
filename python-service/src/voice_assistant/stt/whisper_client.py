"""
Whisper STT Client

Integrates whisper.cpp as subprocess for speech-to-text transcription
with Core ML acceleration on Apple Silicon.
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import wave

import numpy as np

from .audio_processor import AudioProcessor
from .model_manager import ModelManager, WhisperModel

logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """Word-level timing information for transcription segment"""

    start_ms: int
    end_ms: int
    text: str
    confidence: float = 1.0


@dataclass
class AudioInput:
    """Input audio data for transcription"""

    samples: np.ndarray  # Audio data (16kHz, mono, int16 or float32)
    sample_rate: int = 16000
    language: str = "en"

    def __post_init__(self):
        """Validate audio input"""
        if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError(f"Unsupported sample rate: {self.sample_rate}")

        if len(self.samples.shape) > 1 and self.samples.shape[1] > 1:
            raise ValueError("Audio must be mono (single channel)")


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription"""

    text: str
    language: str
    confidence: float  # 0.0-1.0
    duration_ms: int  # Processing time
    segments: List[Segment] = field(default_factory=list)
    model_used: str = ""
    cache_hit: bool = False

    def __post_init__(self):
        """Clean up transcription text"""
        self.text = self.text.strip()


class WhisperSTT:
    """
    Speech-to-Text engine using whisper.cpp with Core ML acceleration

    Features:
    - Subprocess integration with whisper.cpp
    - Core ML acceleration on Apple Silicon
    - VAD preprocessing for better accuracy
    - Result caching for development/testing
    - Multiple model support (base/small/medium)
    """

    def __init__(
        self,
        whisper_cpp_path: Optional[Path] = None,
        model: WhisperModel = WhisperModel.SMALL_EN,
        enable_cache: bool = True,
        cache_dir: Optional[Path] = None,
        language: str = "en",
        num_threads: int = 4,
        enable_vad: bool = True,
    ):
        """
        Initialize Whisper STT client

        Args:
            whisper_cpp_path: Path to whisper.cpp executable
            model: Whisper model to use
            enable_cache: Enable result caching
            cache_dir: Directory for cached results
            language: Default language code
            num_threads: Number of CPU threads for processing
            enable_vad: Enable Voice Activity Detection preprocessing
        """
        self.model = model
        self.language = language
        self.num_threads = num_threads
        self.enable_cache = enable_cache
        self.enable_vad = enable_vad

        # Setup paths
        self.model_manager = ModelManager(whisper_cpp_path=whisper_cpp_path)
        self.whisper_cpp_path = self.model_manager.whisper_cpp_path
        self.audio_processor = AudioProcessor()

        # Setup cache
        if cache_dir is None:
            cache_dir = Path.home() / ".voice-assistant" / "stt-cache"
        self.cache_dir = Path(cache_dir)
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Verify installation
        self._verify_installation()

        logger.info(
            f"WhisperSTT initialized: model={model.value}, "
            f"vad={enable_vad}, cache={enable_cache}"
        )

    def _verify_installation(self) -> None:
        """Verify whisper.cpp is installed and model is available"""
        if not self.whisper_cpp_path.exists():
            raise FileNotFoundError(
                f"whisper.cpp not found at {self.whisper_cpp_path}. "
                "Run scripts/setup_whisper.sh to install."
            )

        model_path = self.model_manager.get_model_path(self.model)
        if not model_path.exists():
            logger.warning(
                f"Model {self.model.value} not found. Downloading..."
            )
            self.model_manager.download_model(self.model)

    def _get_cache_key(self, audio: AudioInput) -> str:
        """Generate cache key from audio data"""
        hasher = hashlib.sha256()
        hasher.update(audio.samples.tobytes())
        hasher.update(f"{audio.sample_rate}".encode())
        hasher.update(audio.language.encode())
        hasher.update(self.model.value.encode())
        return hasher.hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[TranscriptionResult]:
        """Retrieve cached transcription result"""
        if not self.enable_cache:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            result = TranscriptionResult(
                text=data['text'],
                language=data['language'],
                confidence=data['confidence'],
                duration_ms=data['duration_ms'],
                segments=[Segment(**s) for s in data.get('segments', [])],
                model_used=data.get('model_used', ''),
                cache_hit=True,
            )
            logger.debug(f"Cache hit for {cache_key[:8]}...")
            return result
        except Exception as e:
            logger.warning(f"Failed to load cached result: {e}")
            return None

    def _save_to_cache(self, cache_key: str, result: TranscriptionResult) -> None:
        """Save transcription result to cache"""
        if not self.enable_cache:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            data = {
                'text': result.text,
                'language': result.language,
                'confidence': result.confidence,
                'duration_ms': result.duration_ms,
                'segments': [
                    {
                        'start_ms': s.start_ms,
                        'end_ms': s.end_ms,
                        'text': s.text,
                        'confidence': s.confidence,
                    }
                    for s in result.segments
                ],
                'model_used': result.model_used,
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cached result for {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    def _save_audio_to_wav(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        filepath: Path
    ) -> None:
        """Save numpy audio array to WAV file"""
        # Ensure audio is int16
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            # Normalize to [-1, 1] and convert to int16
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data = (audio_data * 32767).astype(np.int16)
        elif audio_data.dtype != np.int16:
            audio_data = audio_data.astype(np.int16)

        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        with wave.open(str(filepath), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    def _execute_whisper_cpp(
        self,
        audio_file: Path,
        language: str,
    ) -> Dict[str, Any]:
        """
        Execute whisper.cpp subprocess and parse output

        Args:
            audio_file: Path to WAV file
            language: Language code

        Returns:
            Dictionary with transcription results
        """
        model_path = self.model_manager.get_model_path(self.model)

        # Build command
        cmd = [
            str(self.whisper_cpp_path),
            "-m", str(model_path),
            "-f", str(audio_file),
            "-l", language,
            "-t", str(self.num_threads),
            "--output-json",
            "--print-colors",
            "--no-timestamps",  # Faster processing
        ]

        # Add Core ML flag if available
        if self.model_manager.has_coreml_model(self.model):
            cmd.extend(["--coreml", str(self.model_manager.get_coreml_path(self.model))])
            logger.debug("Using Core ML acceleration")

        logger.debug(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                check=True,
            )

            # Parse output
            # whisper.cpp outputs to stderr by default
            output = result.stderr + result.stdout

            # Extract transcription from output
            # Look for lines without timestamps
            transcription_lines = []
            for line in output.split('\n'):
                line = line.strip()
                # Skip empty lines, timestamps, and metadata
                if (
                    line and
                    not line.startswith('[') and
                    not line.startswith('whisper_') and
                    not line.startswith('system_info') and
                    not line.startswith('main:') and
                    'processing' not in line.lower() and
                    'load time' not in line.lower()
                ):
                    transcription_lines.append(line)

            transcription = ' '.join(transcription_lines).strip()

            # If no transcription found, try JSON output
            if not transcription:
                json_file = audio_file.with_suffix('.json')
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                        transcription = json_data.get('transcription', '')
                    json_file.unlink()  # Clean up

            return {
                'text': transcription,
                'language': language,
                'success': True,
            }

        except subprocess.TimeoutExpired:
            logger.error("Whisper.cpp execution timed out")
            return {
                'text': '',
                'language': language,
                'success': False,
                'error': 'timeout',
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Whisper.cpp failed: {e.stderr}")
            return {
                'text': '',
                'language': language,
                'success': False,
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error executing whisper.cpp: {e}")
            return {
                'text': '',
                'language': language,
                'success': False,
                'error': str(e),
            }

    def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        """
        Transcribe audio to text

        Args:
            audio: Input audio data

        Returns:
            TranscriptionResult with transcription and metadata

        Raises:
            ValueError: If audio is invalid
            RuntimeError: If transcription fails
        """
        start_time = time.time()

        # Check cache
        cache_key = self._get_cache_key(audio)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        # Preprocess audio
        processed_audio = audio.samples
        if self.enable_vad:
            logger.debug("Applying VAD preprocessing")
            speech_segments = self.audio_processor.extract_speech(
                processed_audio,
                audio.sample_rate
            )
            if len(speech_segments) == 0:
                logger.warning("No speech detected in audio")
                return TranscriptionResult(
                    text="",
                    language=audio.language,
                    confidence=0.0,
                    duration_ms=int((time.time() - start_time) * 1000),
                    model_used=self.model.value,
                )
            processed_audio = speech_segments

        # Normalize audio
        processed_audio = self.audio_processor.normalize_audio(processed_audio)

        # Resample if needed
        if audio.sample_rate != 16000:
            logger.debug(f"Resampling from {audio.sample_rate}Hz to 16000Hz")
            processed_audio = self.audio_processor.resample(
                processed_audio,
                audio.sample_rate,
                16000
            )
            target_sample_rate = 16000
        else:
            target_sample_rate = audio.sample_rate

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            self._save_audio_to_wav(processed_audio, target_sample_rate, tmp_path)

            # Execute whisper.cpp
            result = self._execute_whisper_cpp(tmp_path, audio.language)

            if not result['success']:
                raise RuntimeError(f"Transcription failed: {result.get('error', 'unknown')}")

            # Calculate confidence (simplified - whisper.cpp doesn't provide this directly)
            # We estimate based on text length and success
            confidence = 0.95 if len(result['text']) > 0 else 0.0

            duration_ms = int((time.time() - start_time) * 1000)

            transcription_result = TranscriptionResult(
                text=result['text'],
                language=result['language'],
                confidence=confidence,
                duration_ms=duration_ms,
                model_used=self.model.value,
            )

            # Cache result
            self._save_to_cache(cache_key, transcription_result)

            logger.info(
                f"Transcription completed in {duration_ms}ms: "
                f"\"{transcription_result.text[:50]}...\""
            )

            return transcription_result

        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()

    async def transcribe_async(self, audio: AudioInput) -> TranscriptionResult:
        """
        Async wrapper for transcription (runs in thread pool)

        Args:
            audio: Input audio data

        Returns:
            TranscriptionResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio)

    def clear_cache(self) -> int:
        """
        Clear transcription cache

        Returns:
            Number of cache files deleted
        """
        if not self.enable_cache or not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cached transcriptions")
        return count
