"""
Audio Processor

Handles audio preprocessing for speech-to-text:
- Voice Activity Detection (VAD)
- Audio normalization
- Format conversion
- Resampling
"""

import logging
from typing import Optional, Tuple

import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Audio preprocessing for STT

    Features:
    - Voice Activity Detection using energy-based approach
    - Audio normalization
    - Resampling
    - Format conversion
    """

    def __init__(
        self,
        vad_threshold: float = 0.02,
        vad_min_speech_duration_ms: int = 100,
        vad_padding_ms: int = 200,
    ):
        """
        Initialize audio processor

        Args:
            vad_threshold: Energy threshold for VAD (0.0-1.0)
            vad_min_speech_duration_ms: Minimum speech segment duration
            vad_padding_ms: Padding around speech segments
        """
        self.vad_threshold = vad_threshold
        self.vad_min_speech_duration_ms = vad_min_speech_duration_ms
        self.vad_padding_ms = vad_padding_ms

    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1.0, 1.0] range

        Args:
            audio: Input audio (int16 or float32)

        Returns:
            Normalized audio as float32
        """
        # Convert to float32 if needed
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype == np.int32:
            audio = audio.astype(np.float32) / 2147483648.0
        elif audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Ensure mono
        if len(audio.shape) > 1:
            audio = audio[:, 0]

        # Normalize to [-1, 1]
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val

        return audio

    def calculate_energy(
        self,
        audio: np.ndarray,
        frame_length: int = 512,
    ) -> np.ndarray:
        """
        Calculate energy for VAD

        Args:
            audio: Input audio
            frame_length: Frame length for energy calculation

        Returns:
            Energy values per frame
        """
        # Ensure audio is float
        if audio.dtype != np.float32:
            audio = self.normalize_audio(audio)

        # Calculate energy per frame
        num_frames = len(audio) // frame_length
        energy = np.zeros(num_frames)

        for i in range(num_frames):
            frame = audio[i * frame_length:(i + 1) * frame_length]
            energy[i] = np.sqrt(np.mean(frame ** 2))

        return energy

    def detect_speech_segments(
        self,
        audio: np.ndarray,
        sample_rate: int,
    ) -> list[Tuple[int, int]]:
        """
        Detect speech segments using energy-based VAD

        Args:
            audio: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            List of (start_sample, end_sample) tuples for speech segments
        """
        # Normalize audio
        audio = self.normalize_audio(audio)

        # Calculate energy
        frame_length = int(sample_rate * 0.025)  # 25ms frames
        energy = self.calculate_energy(audio, frame_length)

        # Detect speech frames
        speech_frames = energy > self.vad_threshold

        # Find continuous speech segments
        segments = []
        in_speech = False
        start_frame = 0

        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                # Speech started
                start_frame = i
                in_speech = True
            elif not is_speech and in_speech:
                # Speech ended
                end_frame = i
                in_speech = False

                # Check minimum duration
                duration_ms = (end_frame - start_frame) * frame_length / sample_rate * 1000
                if duration_ms >= self.vad_min_speech_duration_ms:
                    # Add padding
                    padding_frames = int(self.vad_padding_ms / 1000 * sample_rate / frame_length)
                    start_sample = max(0, (start_frame - padding_frames) * frame_length)
                    end_sample = min(len(audio), (end_frame + padding_frames) * frame_length)
                    segments.append((start_sample, end_sample))

        # Handle case where speech continues to end
        if in_speech:
            end_frame = len(speech_frames)
            duration_ms = (end_frame - start_frame) * frame_length / sample_rate * 1000
            if duration_ms >= self.vad_min_speech_duration_ms:
                padding_frames = int(self.vad_padding_ms / 1000 * sample_rate / frame_length)
                start_sample = max(0, (start_frame - padding_frames) * frame_length)
                end_sample = len(audio)
                segments.append((start_sample, end_sample))

        logger.debug(f"Detected {len(segments)} speech segments")
        return segments

    def extract_speech(
        self,
        audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """
        Extract speech portions from audio using VAD

        Args:
            audio: Input audio
            sample_rate: Sample rate in Hz

        Returns:
            Audio with only speech segments (concatenated)
        """
        segments = self.detect_speech_segments(audio, sample_rate)

        if not segments:
            logger.warning("No speech detected")
            return np.array([], dtype=audio.dtype)

        # Concatenate all speech segments
        speech_parts = []
        for start, end in segments:
            speech_parts.append(audio[start:end])

        speech_audio = np.concatenate(speech_parts)

        logger.debug(
            f"Extracted {len(speech_audio)} samples from {len(audio)} "
            f"({len(speech_audio) / len(audio) * 100:.1f}%)"
        )

        return speech_audio

    def resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int,
    ) -> np.ndarray:
        """
        Resample audio to target sample rate

        Args:
            audio: Input audio
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio

        # Calculate resampling ratio
        num_samples = int(len(audio) * target_sr / orig_sr)

        # Use scipy's resample for high-quality resampling
        resampled = signal.resample(audio, num_samples)

        logger.debug(f"Resampled from {orig_sr}Hz to {target_sr}Hz")

        return resampled.astype(audio.dtype)

    def trim_silence(
        self,
        audio: np.ndarray,
        sample_rate: int,
        threshold: Optional[float] = None,
    ) -> np.ndarray:
        """
        Trim silence from beginning and end of audio

        Args:
            audio: Input audio
            sample_rate: Sample rate in Hz
            threshold: Energy threshold (uses VAD threshold if None)

        Returns:
            Trimmed audio
        """
        if threshold is None:
            threshold = self.vad_threshold

        # Normalize audio
        audio = self.normalize_audio(audio)

        # Calculate energy
        frame_length = int(sample_rate * 0.025)  # 25ms frames
        energy = self.calculate_energy(audio, frame_length)

        # Find first and last speech frame
        speech_frames = np.where(energy > threshold)[0]

        if len(speech_frames) == 0:
            logger.warning("No speech detected, returning empty audio")
            return np.array([], dtype=audio.dtype)

        start_frame = speech_frames[0]
        end_frame = speech_frames[-1] + 1

        start_sample = start_frame * frame_length
        end_sample = min(len(audio), end_frame * frame_length)

        return audio[start_sample:end_sample]

    def apply_high_pass_filter(
        self,
        audio: np.ndarray,
        sample_rate: int,
        cutoff_freq: int = 80,
    ) -> np.ndarray:
        """
        Apply high-pass filter to remove low-frequency noise

        Args:
            audio: Input audio
            sample_rate: Sample rate in Hz
            cutoff_freq: Cutoff frequency in Hz

        Returns:
            Filtered audio
        """
        # Design high-pass filter
        nyquist = sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist

        b, a = signal.butter(4, normalized_cutoff, btype='high')

        # Apply filter
        filtered = signal.filtfilt(b, a, audio)

        return filtered.astype(audio.dtype)

    def preprocess_for_stt(
        self,
        audio: np.ndarray,
        sample_rate: int,
        enable_vad: bool = True,
        enable_filter: bool = False,
        target_sr: int = 16000,
    ) -> np.ndarray:
        """
        Complete preprocessing pipeline for STT

        Args:
            audio: Input audio
            sample_rate: Sample rate in Hz
            enable_vad: Enable VAD preprocessing
            enable_filter: Enable high-pass filter
            target_sr: Target sample rate

        Returns:
            Preprocessed audio
        """
        # Normalize
        processed = self.normalize_audio(audio)

        # Apply high-pass filter if enabled
        if enable_filter:
            processed = self.apply_high_pass_filter(processed, sample_rate)

        # Extract speech if VAD enabled
        if enable_vad:
            processed = self.extract_speech(processed, sample_rate)
            if len(processed) == 0:
                return processed

        # Resample to target sample rate
        if sample_rate != target_sr:
            processed = self.resample(processed, sample_rate, target_sr)

        return processed
