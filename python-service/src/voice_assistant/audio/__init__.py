"""
Audio Pipeline Module for Voice Assistant

This module provides:
- Wake word detection using Porcupine
- Continuous audio buffering
- Voice Activity Detection (VAD) using Silero
- Audio device management
- Event-based audio pipeline orchestration

Main exports:
    - AudioEvent: Data class representing audio events
    - AudioEventHandler: Protocol for handling audio events
    - AudioPipeline: Main orchestrator class
"""

from dataclasses import dataclass
from typing import Protocol
import numpy as np

__version__ = "1.0.0"


@dataclass
class AudioEvent:
    """Audio event data structure"""

    type: str  # "wake_word" | "hotkey" | "audio_ready" | "error"
    audio_data: np.ndarray  # Audio samples (16kHz, mono, int16)
    timestamp: float  # Unix timestamp
    duration_seconds: float  # Duration of audio clip
    metadata: dict = None  # Optional metadata (e.g., confidence, device info)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AudioEventHandler(Protocol):
    """Protocol for handling audio events"""

    def on_wake_word_detected(self, event: AudioEvent) -> None:
        """Called when wake word is detected"""
        ...

    def on_audio_ready(self, event: AudioEvent) -> None:
        """Called when complete audio utterance is ready for processing"""
        ...

    def on_error(self, error: Exception) -> None:
        """Called when an error occurs in the audio pipeline"""
        ...


# Import main classes for convenience
from .audio_pipeline import AudioPipeline
from .audio_buffer import CircularAudioBuffer
from .wake_word import WakeWordDetector
from .vad import VoiceActivityDetector
from .device_manager import AudioDeviceManager

__all__ = [
    "AudioEvent",
    "AudioEventHandler",
    "AudioPipeline",
    "CircularAudioBuffer",
    "WakeWordDetector",
    "VoiceActivityDetector",
    "AudioDeviceManager",
]
