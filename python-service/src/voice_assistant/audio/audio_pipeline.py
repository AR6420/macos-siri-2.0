"""
Audio Pipeline Orchestrator

Main audio processing pipeline that coordinates:
- Continuous microphone monitoring
- Wake word detection
- Audio buffering
- Voice Activity Detection
- Hotkey triggering
"""

import asyncio
import numpy as np
import pyaudio
import time
import threading
from typing import Optional, Callable
import logging
from dataclasses import dataclass

from . import AudioEvent, AudioEventHandler
from .audio_buffer import CircularAudioBuffer
from .wake_word import WakeWordDetector, MockWakeWordDetector
from .vad import VoiceActivityDetector
from .device_manager import AudioDeviceManager

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio pipeline configuration"""

    # Wake word settings
    wake_word_enabled: bool = True
    wake_word_access_key: str = ""
    wake_word_model_path: Optional[str] = None
    wake_word_sensitivity: float = 0.5

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 512  # Samples per read (must match Porcupine frame_length)
    buffer_duration_seconds: float = 3.0

    # Device settings
    device_name: Optional[str] = None
    device_index: Optional[int] = None

    # VAD settings
    vad_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 500
    max_utterance_seconds: float = 30.0

    # Hotkey settings
    hotkey_enabled: bool = True  # Future: integrate with keyboard listener


class AudioPipeline:
    """
    Main audio processing pipeline.

    Orchestrates continuous audio monitoring, wake word detection,
    buffering, and VAD to produce AudioEvent objects for downstream
    processing.

    Usage:
        config = AudioConfig(wake_word_access_key="YOUR_KEY")
        pipeline = AudioPipeline(config)

        async def on_audio_ready(event: AudioEvent):
            print(f"Transcribe: {event.duration_seconds}s audio")

        await pipeline.start(on_audio_ready=on_audio_ready)
    """

    def __init__(self, config: AudioConfig):
        """
        Initialize audio pipeline.

        Args:
            config: Audio pipeline configuration
        """
        self.config = config
        self.is_running = False
        self._stop_event = threading.Event()

        # Components
        self.device_manager = AudioDeviceManager()
        self.circular_buffer = CircularAudioBuffer(
            duration_seconds=config.buffer_duration_seconds,
            sample_rate=config.sample_rate,
            channels=config.channels
        )

        # Initialize wake word detector
        if config.wake_word_enabled and config.wake_word_access_key:
            try:
                self.wake_word = WakeWordDetector(
                    access_key=config.wake_word_access_key,
                    keyword_path=config.wake_word_model_path,
                    sensitivity=config.wake_word_sensitivity
                )
                # Update chunk size to match Porcupine requirements
                self.config.chunk_size = self.wake_word.frame_length
                logger.info(
                    f"Wake word detector initialized, "
                    f"chunk_size adjusted to {self.config.chunk_size}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize wake word detector: {e}")
                logger.warning("Using mock wake word detector")
                self.wake_word = MockWakeWordDetector()
        else:
            logger.warning("Wake word detection disabled (no access key)")
            self.wake_word = MockWakeWordDetector()

        # Initialize VAD
        self.vad = VoiceActivityDetector(
            sample_rate=config.sample_rate,
            threshold=config.vad_threshold,
            min_speech_duration_ms=config.min_speech_duration_ms,
            min_silence_duration_ms=config.min_silence_duration_ms
        )

        # Audio stream
        self.pyaudio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.selected_device: Optional[dict] = None

        # State
        self._listening_mode = False  # True when actively recording utterance
        self._utterance_buffer = []  # Accumulates audio after wake word
        self._utterance_start_time = 0.0

        # Event handlers
        self._on_wake_word: Optional[Callable] = None
        self._on_audio_ready: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

        # Hotkey state (will be integrated with keyboard listener)
        self._hotkey_triggered = False

        logger.info(f"Audio pipeline initialized: {config}")

    async def start(
        self,
        on_wake_word: Optional[Callable[[AudioEvent], None]] = None,
        on_audio_ready: Optional[Callable[[AudioEvent], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """
        Start the audio pipeline.

        Args:
            on_wake_word: Callback when wake word detected
            on_audio_ready: Callback when complete utterance ready
            on_error: Callback for errors
        """
        if self.is_running:
            logger.warning("Audio pipeline already running")
            return

        self._on_wake_word = on_wake_word
        self._on_audio_ready = on_audio_ready
        self._on_error = on_error

        # Select audio device
        try:
            self.selected_device = self.device_manager.select_device(
                device_name=self.config.device_name,
                device_index=self.config.device_index
            )
        except Exception as e:
            logger.error(f"Failed to select audio device: {e}")
            if self._on_error:
                self._on_error(e)
            return

        # Open audio stream
        try:
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.selected_device['index'],
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback
            )

            self.stream.start_stream()
            self.is_running = True
            self._stop_event.clear()

            logger.info(
                f"Audio pipeline started on device: {self.selected_device['name']}"
            )

        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            if self._on_error:
                self._on_error(e)
            raise

    def stop(self) -> None:
        """Stop the audio pipeline."""
        if not self.is_running:
            return

        logger.info("Stopping audio pipeline...")
        self.is_running = False
        self._stop_event.set()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        logger.info("Audio pipeline stopped")

    def trigger_hotkey(self) -> None:
        """
        Manually trigger listening mode (simulates wake word).

        Call this from keyboard hotkey handler (e.g., Cmd+Shift+Space).
        """
        logger.info("Hotkey triggered - starting listening mode")
        self._hotkey_triggered = True

    def _audio_callback(
        self,
        in_data,
        frame_count,
        time_info,
        status
    ):
        """
        PyAudio callback for processing audio chunks.

        This runs in a separate thread managed by PyAudio.
        """
        if status:
            logger.warning(f"PyAudio status: {status}")

        # Convert bytes to numpy array
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)

        # Write to circular buffer (always buffer recent audio)
        self.circular_buffer.write(audio_chunk)

        # Process based on current mode
        if self._listening_mode:
            # Currently recording utterance after wake word
            self._process_utterance_recording(audio_chunk)
        else:
            # Monitoring for wake word or hotkey
            self._process_wake_word_detection(audio_chunk)

        return (None, pyaudio.paContinue)

    def _process_wake_word_detection(self, audio_chunk: np.ndarray) -> None:
        """
        Process audio chunk for wake word detection.

        Args:
            audio_chunk: Audio samples to process
        """
        # Check hotkey trigger
        if self._hotkey_triggered:
            self._hotkey_triggered = False
            self._start_utterance_recording("hotkey")
            return

        # Check wake word
        if self.config.wake_word_enabled:
            try:
                detected = self.wake_word.process_frame(audio_chunk)
                if detected:
                    self._start_utterance_recording("wake_word")
            except Exception as e:
                logger.error(f"Wake word detection error: {e}")
                if self._on_error:
                    self._on_error(e)

    def _start_utterance_recording(self, trigger_type: str) -> None:
        """
        Start recording user utterance.

        Args:
            trigger_type: "wake_word" or "hotkey"
        """
        logger.info(f"Starting utterance recording (trigger: {trigger_type})")

        # Switch to listening mode
        self._listening_mode = True
        self._utterance_buffer = []
        self._utterance_start_time = time.time()

        # Get buffered audio (pre-wake-word context)
        buffered_audio = self.circular_buffer.read_all()

        # Emit wake word event
        if self._on_wake_word:
            event = AudioEvent(
                type=trigger_type,
                audio_data=buffered_audio,
                timestamp=time.time(),
                duration_seconds=self.config.buffer_duration_seconds,
                metadata={"trigger": trigger_type}
            )
            try:
                # Call in thread-safe manner
                asyncio.run_coroutine_threadsafe(
                    self._async_callback(self._on_wake_word, event),
                    asyncio.get_event_loop()
                )
            except Exception as e:
                logger.warning(f"Could not schedule wake word callback: {e}")

        # Reset VAD state
        self.vad.reset()

    def _process_utterance_recording(self, audio_chunk: np.ndarray) -> None:
        """
        Process audio chunk during utterance recording.

        Args:
            audio_chunk: Audio samples to process
        """
        # Add to utterance buffer
        self._utterance_buffer.append(audio_chunk)

        # Check for speech end using VAD
        speech_ended = self.vad.has_speech_ended(
            audio_chunk,
            min_silence_ms=self.config.min_silence_duration_ms
        )

        # Check for max utterance duration
        duration = time.time() - self._utterance_start_time
        max_duration_reached = duration >= self.config.max_utterance_seconds

        if speech_ended or max_duration_reached:
            if max_duration_reached:
                logger.warning(
                    f"Max utterance duration reached: {duration:.1f}s"
                )

            self._finish_utterance_recording()

    def _finish_utterance_recording(self) -> None:
        """Finish recording and emit audio_ready event."""
        logger.info("Utterance recording complete")

        # Exit listening mode
        self._listening_mode = False

        # Concatenate all audio chunks
        if self._utterance_buffer:
            utterance_audio = np.concatenate(self._utterance_buffer)
        else:
            logger.warning("No audio captured in utterance buffer")
            utterance_audio = np.array([], dtype=np.int16)

        duration = len(utterance_audio) / self.config.sample_rate

        # Emit audio ready event
        if self._on_audio_ready:
            event = AudioEvent(
                type="audio_ready",
                audio_data=utterance_audio,
                timestamp=time.time(),
                duration_seconds=duration,
                metadata={
                    "sample_rate": self.config.sample_rate,
                    "channels": self.config.channels
                }
            )

            try:
                # Call in thread-safe manner
                asyncio.run_coroutine_threadsafe(
                    self._async_callback(self._on_audio_ready, event),
                    asyncio.get_event_loop()
                )
            except Exception as e:
                logger.warning(f"Could not schedule audio ready callback: {e}")
                # Fallback to synchronous call
                if asyncio.iscoroutinefunction(self._on_audio_ready):
                    logger.error("Cannot call async callback from thread")
                else:
                    self._on_audio_ready(event)

        # Clear buffer
        self._utterance_buffer = []

    async def _async_callback(self, callback: Callable, *args, **kwargs):
        """
        Wrapper to call both sync and async callbacks.

        Args:
            callback: Callback function (sync or async)
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if asyncio.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)

    def update_wake_word_sensitivity(self, sensitivity: float) -> None:
        """
        Update wake word detection sensitivity.

        Args:
            sensitivity: New sensitivity (0.0-1.0)
        """
        logger.info(f"Updating wake word sensitivity to {sensitivity}")
        self.config.wake_word_sensitivity = sensitivity

        if hasattr(self.wake_word, 'update_sensitivity'):
            self.wake_word.update_sensitivity(sensitivity)

    def get_status(self) -> dict:
        """
        Get current pipeline status.

        Returns:
            Status dictionary with current state
        """
        return {
            "is_running": self.is_running,
            "listening_mode": self._listening_mode,
            "device": self.selected_device['name'] if self.selected_device else None,
            "sample_rate": self.config.sample_rate,
            "wake_word_enabled": self.config.wake_word_enabled,
            "buffer_duration": self.config.buffer_duration_seconds,
            "available_buffer": self.circular_buffer.get_available_duration()
        }

    def close(self) -> None:
        """Cleanup all resources."""
        logger.info("Closing audio pipeline...")

        self.stop()

        if self.wake_word:
            self.wake_word.close()

        if self.device_manager:
            self.device_manager.close()

        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None

        logger.info("Audio pipeline closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def __repr__(self) -> str:
        status = "running" if self.is_running else "stopped"
        mode = "listening" if self._listening_mode else "monitoring"
        return f"AudioPipeline(status={status}, mode={mode})"
