"""
Voice Activity Detection (VAD) using Silero

Detects speech segments in audio to determine when user has finished speaking.
"""

import numpy as np
import torch
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """
    Voice Activity Detection using Silero VAD model.

    Detects speech vs silence in audio to segment utterances.

    Attributes:
        sample_rate: Audio sample rate (must be 8000 or 16000 Hz)
        threshold: Speech probability threshold (0.0-1.0)
        min_speech_duration_ms: Minimum speech duration to consider
        min_silence_duration_ms: Minimum silence to mark end of speech
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 500,
        window_size_samples: int = 512
    ):
        """
        Initialize VAD with Silero model.

        Args:
            sample_rate: Audio sample rate (8000 or 16000 Hz)
            threshold: Speech confidence threshold (0.0-1.0)
            min_speech_duration_ms: Minimum duration to consider as speech
            min_silence_duration_ms: Minimum silence duration to end utterance
            window_size_samples: VAD window size in samples

        Raises:
            ValueError: If sample_rate is not 8000 or 16000
        """
        if sample_rate not in [8000, 16000]:
            raise ValueError(f"Sample rate must be 8000 or 16000 Hz, got {sample_rate}")

        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.window_size_samples = window_size_samples

        # Load Silero VAD model
        try:
            # Load from torch hub
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )

            # Extract utility functions
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = utils

            logger.info("Silero VAD model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            logger.warning("VAD functionality will be limited")
            self.model = None

        # State tracking
        self._is_speaking = False
        self._speech_start_sample = 0
        self._silence_start_sample = 0
        self._total_samples_processed = 0

    def is_speech(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if audio chunk contains speech.

        Args:
            audio_chunk: Audio samples (int16 or float32, mono)

        Returns:
            Tuple of (is_speech: bool, confidence: float)
        """
        if self.model is None:
            # Fallback: simple energy-based detection
            return self._energy_based_vad(audio_chunk)

        # Convert to float32 in range [-1, 1] if needed
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk.astype(np.float32)

        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float)

        # Get speech probability
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.sample_rate).item()

        is_speech = speech_prob >= self.threshold

        return is_speech, speech_prob

    def _energy_based_vad(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """
        Fallback energy-based VAD when Silero model is unavailable.

        Args:
            audio_chunk: Audio samples

        Returns:
            Tuple of (is_speech: bool, confidence: float)
        """
        # Calculate RMS energy
        if audio_chunk.dtype == np.int16:
            audio_float = audio_chunk.astype(np.float32) / 32768.0
        else:
            audio_float = audio_chunk

        rms = np.sqrt(np.mean(audio_float ** 2))

        # Simple threshold-based detection
        energy_threshold = 0.02
        is_speech = rms > energy_threshold
        confidence = min(rms / energy_threshold, 1.0)

        return is_speech, confidence

    def process_audio(
        self,
        audio_data: np.ndarray,
        reset: bool = False
    ) -> list[dict]:
        """
        Process audio and return speech segments.

        Args:
            audio_data: Audio samples (int16 or float32, mono)
            reset: Reset internal state before processing

        Returns:
            List of speech segments: [{"start": sample_idx, "end": sample_idx, "confidence": float}]
        """
        if reset:
            self.reset()

        if self.model is None:
            # Fallback to simple segmentation
            return self._simple_segment(audio_data)

        # Convert to float32 in range [-1, 1] if needed
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        else:
            audio_float = audio_data.astype(np.float32)

        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float)

        # Get speech timestamps
        try:
            speech_timestamps = self.get_speech_timestamps(
                audio_tensor,
                self.model,
                sampling_rate=self.sample_rate,
                threshold=self.threshold,
                min_speech_duration_ms=self.min_speech_duration_ms,
                min_silence_duration_ms=self.min_silence_duration_ms
            )

            # Convert to our format
            segments = [
                {
                    "start": ts["start"],
                    "end": ts["end"],
                    "confidence": 1.0  # Silero doesn't provide confidence per segment
                }
                for ts in speech_timestamps
            ]

            return segments

        except Exception as e:
            logger.error(f"Error processing audio with Silero VAD: {e}")
            return self._simple_segment(audio_data)

    def _simple_segment(self, audio_data: np.ndarray) -> list[dict]:
        """
        Simple energy-based segmentation fallback.

        Args:
            audio_data: Audio samples

        Returns:
            List of speech segments
        """
        segments = []
        window_size = self.window_size_samples
        num_windows = len(audio_data) // window_size

        in_speech = False
        speech_start = 0

        for i in range(num_windows):
            start = i * window_size
            end = start + window_size
            chunk = audio_data[start:end]

            is_speech, confidence = self._energy_based_vad(chunk)

            if is_speech and not in_speech:
                # Speech started
                speech_start = start
                in_speech = True
            elif not is_speech and in_speech:
                # Speech ended
                segments.append({
                    "start": speech_start,
                    "end": start,
                    "confidence": confidence
                })
                in_speech = False

        # Close final segment if still in speech
        if in_speech:
            segments.append({
                "start": speech_start,
                "end": len(audio_data),
                "confidence": 0.5
            })

        return segments

    def has_speech_ended(
        self,
        audio_chunk: np.ndarray,
        min_silence_ms: Optional[int] = None
    ) -> bool:
        """
        Detect if speech has ended based on silence duration.

        Args:
            audio_chunk: Recent audio samples
            min_silence_ms: Minimum silence duration (uses default if None)

        Returns:
            True if speech has ended (sufficient silence detected)
        """
        if min_silence_ms is None:
            min_silence_ms = self.min_silence_duration_ms

        is_speech, _ = self.is_speech(audio_chunk)

        chunk_duration_ms = (len(audio_chunk) / self.sample_rate) * 1000

        if is_speech:
            # Reset silence counter
            self._is_speaking = True
            self._silence_start_sample = 0
            return False
        else:
            # Silence detected
            if self._is_speaking:
                if self._silence_start_sample == 0:
                    self._silence_start_sample = self._total_samples_processed

                # Check if silence duration exceeds threshold
                silence_samples = self._total_samples_processed - self._silence_start_sample
                silence_ms = (silence_samples / self.sample_rate) * 1000

                if silence_ms >= min_silence_ms:
                    self._is_speaking = False
                    return True

        self._total_samples_processed += len(audio_chunk)
        return False

    def reset(self) -> None:
        """Reset VAD state."""
        self._is_speaking = False
        self._speech_start_sample = 0
        self._silence_start_sample = 0
        self._total_samples_processed = 0
        logger.debug("VAD state reset")

    def __repr__(self) -> str:
        model_status = "loaded" if self.model is not None else "fallback"
        return (
            f"VoiceActivityDetector(sample_rate={self.sample_rate}Hz, "
            f"threshold={self.threshold}, model={model_status})"
        )
