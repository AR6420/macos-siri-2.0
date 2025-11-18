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

# Package-level exports
__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # Audio components
    "AudioEvent",
    "AudioEventHandler",
    "AudioPipeline",
]
