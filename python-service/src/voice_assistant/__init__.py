"""
Voice Assistant for macOS

A privacy-first, intelligent voice assistant for macOS Tahoe 26.1 that combines
local AI processing with flexible cloud API support.
"""

__version__ = "1.0.0"
__author__ = "Voice Assistant Contributors"
__license__ = "Apache-2.0"

from typing import Any

# Audio pipeline components (Agent 2)
from .audio import AudioEvent, AudioEventHandler, AudioPipeline

# Orchestration components (Agent 6)
from .orchestrator import VoiceAssistant, AssistantStatus
from .pipeline import VoicePipeline, PipelineResult
from .state import ConversationState, ConversationTurn
from .metrics import MetricsCollector, PerformanceTimer
from .errors import ErrorRecoveryHandler, ErrorType, VoiceAssistantError
from .tts import MacOSTTS, TTSConfig, create_tts_from_config

# Package-level exports
__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # Audio components
    "AudioEvent",
    "AudioEventHandler",
    "AudioPipeline",
    # Orchestration components
    "VoiceAssistant",
    "AssistantStatus",
    "VoicePipeline",
    "PipelineResult",
    "ConversationState",
    "ConversationTurn",
    "MetricsCollector",
    "PerformanceTimer",
    "ErrorRecoveryHandler",
    "ErrorType",
    "VoiceAssistantError",
    "MacOSTTS",
    "TTSConfig",
    "create_tts_from_config",
]
