"""
Wake Word Detection using Porcupine

Integrates Picovoice Porcupine for "Hey Claude" wake word detection.
"""

import os
import struct
from typing import Optional, Callable
import numpy as np
import logging

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    pvporcupine = None

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detector using Porcupine.

    Detects "Hey Claude" wake word in audio stream with configurable sensitivity.

    Attributes:
        sensitivity: Detection sensitivity (0.0 to 1.0)
        sample_rate: Required sample rate for Porcupine (16000 Hz)
        frame_length: Required frame length for Porcupine
    """

    def __init__(
        self,
        access_key: str,
        keyword_path: Optional[str] = None,
        sensitivity: float = 0.5,
        model_path: Optional[str] = None
    ):
        """
        Initialize wake word detector.

        Args:
            access_key: Porcupine access key from Picovoice Console
            keyword_path: Path to custom .ppn wake word file (optional)
            sensitivity: Detection sensitivity (0.0-1.0). Higher = more sensitive.
            model_path: Path to Porcupine model file (optional)

        Raises:
            ImportError: If pvporcupine is not installed
            ValueError: If access_key is invalid or sensitivity out of range
        """
        if not PORCUPINE_AVAILABLE:
            raise ImportError(
                "pvporcupine is not installed. "
                "Install with: pip install pvporcupine"
            )

        if not access_key:
            raise ValueError(
                "Porcupine access_key is required. "
                "Get one from https://console.picovoice.ai/"
            )

        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError(f"Sensitivity must be between 0.0 and 1.0, got {sensitivity}")

        self.sensitivity = sensitivity
        self.access_key = access_key
        self.keyword_path = keyword_path
        self.model_path = model_path

        # Initialize Porcupine
        try:
            kwargs = {"access_key": access_key}

            if keyword_path:
                kwargs["keyword_paths"] = [keyword_path]
                kwargs["sensitivities"] = [sensitivity]
            else:
                # Use built-in keywords if available
                # For custom "Hey Claude", you'll need to train and provide keyword_path
                logger.warning(
                    "No custom keyword_path provided. "
                    "Train a custom 'Hey Claude' wake word at https://console.picovoice.ai/"
                )
                # Fallback to a built-in keyword for testing
                # TODO: Replace with custom "Hey Claude" keyword
                kwargs["keywords"] = ["jarvis"]  # Built-in keyword for testing
                kwargs["sensitivities"] = [sensitivity]

            if model_path:
                kwargs["model_path"] = model_path

            self.porcupine = pvporcupine.create(**kwargs)

        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            raise

        # Store frame requirements
        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length

        # Detection state
        self._detection_callback: Optional[Callable[[float], None]] = None

        logger.info(
            f"Wake word detector initialized: "
            f"sample_rate={self.sample_rate}Hz, "
            f"frame_length={self.frame_length}, "
            f"sensitivity={self.sensitivity}"
        )

    def process_frame(self, audio_frame: np.ndarray) -> bool:
        """
        Process a single audio frame for wake word detection.

        Args:
            audio_frame: Audio samples (must be exactly frame_length samples, int16)

        Returns:
            True if wake word detected, False otherwise

        Raises:
            ValueError: If frame length is incorrect
        """
        if len(audio_frame) != self.frame_length:
            raise ValueError(
                f"Audio frame must be {self.frame_length} samples, "
                f"got {len(audio_frame)}"
            )

        # Convert numpy array to list of ints (Porcupine requirement)
        if audio_frame.dtype != np.int16:
            audio_frame = audio_frame.astype(np.int16)

        pcm = audio_frame.tolist()

        # Process frame
        keyword_index = self.porcupine.process(pcm)

        detected = keyword_index >= 0

        if detected:
            logger.info(f"Wake word detected! (keyword_index={keyword_index})")
            if self._detection_callback:
                self._detection_callback(self.sensitivity)

        return detected

    def process_audio(self, audio_data: np.ndarray) -> list[int]:
        """
        Process audio buffer and return indices where wake word was detected.

        Args:
            audio_data: Audio samples (int16, mono, 16kHz)

        Returns:
            List of sample indices where wake word was detected
        """
        detections = []
        num_frames = len(audio_data) // self.frame_length

        for i in range(num_frames):
            start = i * self.frame_length
            end = start + self.frame_length
            frame = audio_data[start:end]

            if self.process_frame(frame):
                detections.append(start)

        return detections

    def set_detection_callback(self, callback: Callable[[float], None]) -> None:
        """
        Set callback to be called when wake word is detected.

        Args:
            callback: Function to call with sensitivity value when detected
        """
        self._detection_callback = callback

    def update_sensitivity(self, sensitivity: float) -> None:
        """
        Update detection sensitivity.

        Note: This requires recreating the Porcupine instance.

        Args:
            sensitivity: New sensitivity value (0.0-1.0)
        """
        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError(f"Sensitivity must be between 0.0 and 1.0, got {sensitivity}")

        if sensitivity != self.sensitivity:
            logger.info(f"Updating sensitivity from {self.sensitivity} to {sensitivity}")
            self.sensitivity = sensitivity

            # Recreate Porcupine with new sensitivity
            self.close()
            self.__init__(
                access_key=self.access_key,
                keyword_path=self.keyword_path,
                sensitivity=sensitivity,
                model_path=self.model_path
            )

    def close(self) -> None:
        """Release Porcupine resources."""
        if hasattr(self, 'porcupine') and self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None
            logger.info("Wake word detector closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        return (
            f"WakeWordDetector(sensitivity={self.sensitivity}, "
            f"sample_rate={self.sample_rate}Hz, "
            f"frame_length={self.frame_length})"
        )


class MockWakeWordDetector:
    """
    Mock wake word detector for testing without Porcupine.

    Always returns False for detection.
    """

    def __init__(self, *args, **kwargs):
        self.sample_rate = 16000
        self.frame_length = 512
        self.sensitivity = kwargs.get('sensitivity', 0.5)
        logger.warning("Using MockWakeWordDetector - wake word detection disabled")

    def process_frame(self, audio_frame: np.ndarray) -> bool:
        return False

    def process_audio(self, audio_data: np.ndarray) -> list[int]:
        return []

    def set_detection_callback(self, callback: Callable[[float], None]) -> None:
        pass

    def update_sensitivity(self, sensitivity: float) -> None:
        self.sensitivity = sensitivity

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
