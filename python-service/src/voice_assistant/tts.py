"""
Text-to-Speech Module

Provides text-to-speech functionality using macOS native voices (NSSpeechSynthesizer).
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, List
import platform

logger = logging.getLogger(__name__)


@dataclass
class TTSConfig:
    """TTS configuration"""
    engine: str = "macos_native"
    voice: str = "Samantha"
    rate: int = 200  # Words per minute
    volume: float = 0.8  # 0.0 to 1.0
    pitch: float = 1.0  # Pitch multiplier


class MacOSTTS:
    """
    macOS native Text-to-Speech using NSSpeechSynthesizer via PyObjC.

    Features:
    - Native macOS voices
    - Asynchronous speech with callbacks
    - Rate, volume, and pitch control
    - Speech interruption support
    """

    def __init__(self, config: Optional[TTSConfig] = None):
        """
        Initialize macOS TTS engine.

        Args:
            config: TTS configuration (defaults to Samantha voice at 200 WPM)
        """
        self.config = config or TTSConfig()
        self._synth = None
        self._is_speaking = False
        self._speech_complete_event: Optional[asyncio.Event] = None

        # Only initialize PyObjC on macOS
        if platform.system() == "Darwin":
            try:
                from AppKit import NSSpeechSynthesizer
                self._NSSpeechSynthesizer = NSSpeechSynthesizer
                self._init_synthesizer()
                logger.info(f"macOS TTS initialized with voice: {self.config.voice}")
            except ImportError:
                logger.warning("PyObjC not available, TTS will not work")
                self._NSSpeechSynthesizer = None
        else:
            logger.warning("macOS TTS only works on macOS, using mock mode")
            self._NSSpeechSynthesizer = None

    def _init_synthesizer(self):
        """Initialize the NSSpeechSynthesizer"""
        if self._NSSpeechSynthesizer is None:
            return

        self._synth = self._NSSpeechSynthesizer.alloc().initWithVoice_(
            self.config.voice
        )

        if self._synth is None:
            # Fallback to default voice
            logger.warning(f"Voice '{self.config.voice}' not found, using default")
            self._synth = self._NSSpeechSynthesizer.alloc().init()

        # Set rate (words per minute)
        self._synth.setRate_(self.config.rate)

        # Set volume (0.0 to 1.0)
        self._synth.setVolume_(self.config.volume)

    async def speak(self, text: str, wait: bool = True) -> None:
        """
        Speak the given text.

        Args:
            text: Text to speak
            wait: If True, wait for speech to complete before returning

        Raises:
            RuntimeError: If TTS is not available
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS, skipping")
            return

        if self._NSSpeechSynthesizer is None:
            logger.warning(f"TTS not available, would speak: {text}")
            return

        # Stop any current speech
        if self._is_speaking:
            await self.stop()

        logger.info(f"Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")

        self._is_speaking = True

        if wait:
            # Create event for async waiting
            self._speech_complete_event = asyncio.Event()

            # Start speaking in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._speak_sync,
                text
            )

            # Wait for completion
            await self._speech_complete_event.wait()
        else:
            # Fire and forget
            self._synth.startSpeakingString_(text)

    def _speak_sync(self, text: str):
        """Synchronous speech (blocking)"""
        try:
            # This blocks until speech is complete
            self._synth.startSpeakingString_(text)

            # Wait for speech to finish
            while self._synth.isSpeaking():
                import time
                time.sleep(0.1)

        finally:
            self._is_speaking = False
            if self._speech_complete_event:
                # Use call_soon_threadsafe since we're in executor thread
                import asyncio
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(self._speech_complete_event.set)

    async def stop(self) -> None:
        """Stop current speech"""
        if self._synth and self._is_speaking:
            logger.info("Stopping speech")
            self._synth.stopSpeaking()
            self._is_speaking = False
            if self._speech_complete_event:
                self._speech_complete_event.set()

    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self._is_speaking

    @staticmethod
    def get_available_voices() -> List[str]:
        """
        Get list of available system voices.

        Returns:
            List of voice names
        """
        if platform.system() != "Darwin":
            return []

        try:
            from AppKit import NSSpeechSynthesizer
            voices = NSSpeechSynthesizer.availableVoices()
            return [str(v).split('.')[-1] for v in voices]
        except ImportError:
            return []

    def set_voice(self, voice: str) -> bool:
        """
        Change the voice.

        Args:
            voice: Voice name

        Returns:
            True if voice was changed successfully
        """
        if self._NSSpeechSynthesizer is None:
            return False

        old_voice = self.config.voice
        self.config.voice = voice

        # Reinitialize synthesizer with new voice
        self._init_synthesizer()

        if self._synth is None:
            logger.error(f"Failed to set voice to {voice}, reverting to {old_voice}")
            self.config.voice = old_voice
            self._init_synthesizer()
            return False

        logger.info(f"Voice changed from {old_voice} to {voice}")
        return True

    def set_rate(self, rate: int) -> None:
        """
        Set speech rate.

        Args:
            rate: Words per minute (typically 170-210)
        """
        self.config.rate = max(90, min(400, rate))  # Clamp to reasonable range
        if self._synth:
            self._synth.setRate_(self.config.rate)
        logger.info(f"Speech rate set to {self.config.rate} WPM")

    def set_volume(self, volume: float) -> None:
        """
        Set speech volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.config.volume = max(0.0, min(1.0, volume))
        if self._synth:
            self._synth.setVolume_(self.config.volume)
        logger.info(f"Speech volume set to {self.config.volume}")

    async def close(self) -> None:
        """Clean up resources"""
        await self.stop()
        self._synth = None
        logger.info("TTS closed")


# Factory function for creating TTS from config
def create_tts_from_config(config: dict) -> MacOSTTS:
    """
    Create TTS instance from configuration dictionary.

    Args:
        config: Configuration dictionary with 'tts' section

    Returns:
        MacOSTTS instance
    """
    tts_config_dict = config.get("tts", {}).get("macos", {})

    tts_config = TTSConfig(
        engine=config.get("tts", {}).get("engine", "macos_native"),
        voice=tts_config_dict.get("voice", "Samantha"),
        rate=tts_config_dict.get("rate", 200),
        volume=tts_config_dict.get("volume", 0.8),
        pitch=tts_config_dict.get("pitch", 1.0),
    )

    return MacOSTTS(tts_config)
