"""
Speech-to-Text Module

Provides speech-to-text transcription using whisper.cpp with Core ML acceleration.
"""

from .whisper_client import WhisperSTT, AudioInput, TranscriptionResult, Segment
from .audio_processor import AudioProcessor
from .model_manager import ModelManager, WhisperModel

__all__ = [
    "WhisperSTT",
    "AudioInput",
    "TranscriptionResult",
    "Segment",
    "AudioProcessor",
    "ModelManager",
    "WhisperModel",
]
