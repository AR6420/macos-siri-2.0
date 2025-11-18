"""
Voice Assistant Orchestrator

Main coordinator that brings together all subsystems and manages
the complete voice assistant lifecycle.
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum

from .audio import AudioEvent, AudioEventHandler, AudioPipeline
from .stt import WhisperSTT, WhisperModel
from .llm import ProviderFactory, LLMProvider
from .tts import MacOSTTS, create_tts_from_config
from .state import ConversationState
from .metrics import MetricsCollector
from .errors import ErrorRecoveryHandler
from .pipeline import VoicePipeline, PipelineResult

logger = logging.getLogger(__name__)


class AssistantStatus(str, Enum):
    """Voice assistant status states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"
    INITIALIZING = "initializing"
    STOPPED = "stopped"


class VoiceAssistant:
    """
    Main Voice Assistant Orchestrator

    Coordinates all subsystems:
    - Audio pipeline (wake word, VAD, buffering)
    - Speech-to-text (Whisper)
    - LLM (local or cloud providers)
    - MCP tools (macOS automation)
    - Text-to-speech (macOS voices)
    - Conversation state
    - Metrics and error recovery

    Features:
    - Event-driven architecture
    - Asynchronous pipeline processing
    - Status callbacks for UI updates
    - Graceful error recovery
    - Performance monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Voice Assistant.

        Args:
            config: Configuration dictionary loaded from config.yaml
        """
        self.config = config
        self._status = AssistantStatus.INITIALIZING
        self._running = False

        # Status callback for UI updates
        self._status_callback: Optional[Callable] = None

        # Initialize subsystems (will be set in _initialize_subsystems)
        self.audio_pipeline: Optional[AudioPipeline] = None
        self.stt: Optional[WhisperSTT] = None
        self.llm: Optional[LLMProvider] = None
        self.tts: Optional[MacOSTTS] = None
        self.mcp_client: Optional[Any] = None
        self.conversation_state: Optional[ConversationState] = None
        self.metrics: Optional[MetricsCollector] = None
        self.error_handler: Optional[ErrorRecoveryHandler] = None
        self.pipeline: Optional[VoicePipeline] = None

        logger.info("Voice Assistant orchestrator created")

    async def initialize(self) -> bool:
        """
        Initialize all subsystems.

        Returns:
            True if initialization successful

        Raises:
            Exception if critical subsystems fail to initialize
        """
        try:
            logger.info("Initializing Voice Assistant subsystems...")

            # Initialize metrics first (needed by other components)
            await self._initialize_metrics()

            # Initialize TTS early (needed for error messages)
            await self._initialize_tts()

            # Initialize error handler
            await self._initialize_error_handler()

            # Initialize conversation state
            await self._initialize_conversation_state()

            # Initialize LLM provider
            await self._initialize_llm()

            # Initialize STT
            await self._initialize_stt()

            # Initialize MCP client (optional)
            await self._initialize_mcp()

            # Initialize audio pipeline
            await self._initialize_audio()

            # Create pipeline coordinator
            await self._initialize_pipeline()

            self._status = AssistantStatus.IDLE
            logger.info("Voice Assistant initialized successfully")

            return True

        except Exception as e:
            logger.exception(f"Failed to initialize Voice Assistant: {e}")
            self._status = AssistantStatus.ERROR
            raise

    async def _initialize_metrics(self) -> None:
        """Initialize metrics collector"""
        perf_config = self.config.get("performance", {})

        self.metrics = MetricsCollector(
            enable_metrics=perf_config.get("enable_metrics", True),
            log_interval_seconds=perf_config.get("metrics_log_interval_seconds", 60),
        )

        # Start periodic logging
        await self.metrics.start_periodic_logging()

        logger.info("Metrics collector initialized")

    async def _initialize_tts(self) -> None:
        """Initialize text-to-speech"""
        self.tts = create_tts_from_config(self.config)
        logger.info("TTS initialized")

    async def _initialize_error_handler(self) -> None:
        """Initialize error recovery handler"""
        self.error_handler = ErrorRecoveryHandler(
            config=self.config,
            tts_engine=self.tts,
            fallback_provider=None,  # TODO: Initialize fallback provider
        )
        logger.info("Error handler initialized")

    async def _initialize_conversation_state(self) -> None:
        """Initialize conversation state manager"""
        conv_config = self.config.get("conversation", {})

        self.conversation_state = ConversationState(
            max_turns=conv_config.get("max_history_turns", 10),
            max_context_tokens=conv_config.get("context_window_tokens", 4096),
            system_prompt=conv_config.get("system_prompt"),
            session_timeout_minutes=conv_config.get("context", {}).get(
                "session_timeout_minutes", 30
            ),
        )
        logger.info("Conversation state initialized")

    async def _initialize_llm(self) -> None:
        """Initialize LLM provider"""
        try:
            self.llm = ProviderFactory.create_from_config(self.config)
            logger.info(f"LLM provider initialized: {self.llm}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    async def _initialize_stt(self) -> None:
        """Initialize speech-to-text"""
        stt_config = self.config.get("stt", {}).get("whisper", {})

        # Map model name to enum
        model_name = stt_config.get("model", "small.en")
        model_map = {
            "tiny.en": WhisperModel.TINY_EN,
            "base.en": WhisperModel.BASE_EN,
            "small.en": WhisperModel.SMALL_EN,
            "medium.en": WhisperModel.MEDIUM_EN,
            "large": WhisperModel.LARGE,
        }
        model = model_map.get(model_name, WhisperModel.SMALL_EN)

        self.stt = WhisperSTT(
            whisper_cpp_path=Path(stt_config.get("binary_path", "")).parent.parent
            if stt_config.get("binary_path")
            else None,
            model=model,
            enable_cache=self.config.get("performance", {}).get("cache", {}).get("enabled", True),
            language=stt_config.get("language", "en"),
            num_threads=stt_config.get("threads", 4),
            enable_vad=self.config.get("stt", {}).get("preprocessing", {}).get("vad_filter", True),
        )
        logger.info("STT initialized")

    async def _initialize_mcp(self) -> None:
        """Initialize MCP client (optional)"""
        # MCP client will be implemented by Agent 5
        # For now, leave as None
        self.mcp_client = None
        logger.info("MCP client not initialized (optional)")

    async def _initialize_audio(self) -> None:
        """Initialize audio pipeline"""
        # Audio pipeline will be provided by Agent 2
        # For now, create placeholder
        self.audio_pipeline = None
        logger.info("Audio pipeline placeholder (to be initialized by Agent 2)")

    async def _initialize_pipeline(self) -> None:
        """Initialize pipeline coordinator"""
        self.pipeline = VoicePipeline(
            stt=self.stt,
            llm_provider=self.llm,
            tts=self.tts,
            conversation_state=self.conversation_state,
            metrics=self.metrics,
            error_handler=self.error_handler,
            config=self.config,
            mcp_client=self.mcp_client,
        )
        logger.info("Voice pipeline initialized")

    async def start(self) -> None:
        """
        Start the voice assistant (begin listening for wake word).
        """
        if self._running:
            logger.warning("Voice assistant already running")
            return

        if self._status != AssistantStatus.IDLE:
            logger.error(f"Cannot start from status: {self._status}")
            return

        logger.info("Starting Voice Assistant...")

        self._running = True
        self._update_status(AssistantStatus.LISTENING)

        # Start audio pipeline if available
        if self.audio_pipeline:
            await self.audio_pipeline.start(
                on_wake_word=self._handle_wake_word,
                on_audio_ready=self._handle_audio_ready
            )
            logger.info("Audio pipeline started, listening for wake word...")
        else:
            logger.warning("Audio pipeline not available, voice assistant in limited mode")

    async def stop(self) -> None:
        """
        Stop the voice assistant.
        """
        if not self._running:
            logger.warning("Voice assistant not running")
            return

        logger.info("Stopping Voice Assistant...")

        self._running = False

        # Stop audio pipeline
        if self.audio_pipeline:
            await self.audio_pipeline.stop()

        # Stop TTS if speaking
        if self.tts and self.tts.is_speaking():
            await self.tts.stop()

        # Stop metrics logging
        if self.metrics:
            await self.metrics.stop_periodic_logging()

        self._update_status(AssistantStatus.STOPPED)
        logger.info("Voice Assistant stopped")

    async def cleanup(self) -> None:
        """
        Clean up resources.
        """
        logger.info("Cleaning up Voice Assistant...")

        await self.stop()

        # Close LLM provider
        if self.llm:
            await self.llm.close()

        # Close TTS
        if self.tts:
            await self.tts.close()

        logger.info("Voice Assistant cleanup complete")

    # Event handlers (called by audio pipeline)

    async def _handle_wake_word(self, event: AudioEvent) -> None:
        """
        Handle wake word detection.

        Args:
            event: Audio event from wake word detection
        """
        logger.info("Wake word detected!")
        self._update_status(AssistantStatus.LISTENING)

        # Emit event to UI
        await self._emit_event({
            "type": "wake_word_detected",
            "timestamp": event.timestamp,
        })

    async def _handle_audio_ready(self, event: AudioEvent) -> None:
        """
        Handle complete audio utterance ready for processing.

        This is the main pipeline entry point.

        Args:
            event: Audio event with complete utterance
        """
        logger.info(f"Audio ready: {event.duration_seconds:.1f}s")

        self._update_status(AssistantStatus.PROCESSING)

        # Process through pipeline
        result = await self.pipeline.process_audio_event(event)

        # Emit result to UI
        await self._emit_event({
            "type": "processing_complete",
            "success": result.success,
            "transcription": result.transcription,
            "response": result.response,
            "error": result.error,
            "duration_ms": result.duration_ms,
        })

        # Back to listening
        self._update_status(AssistantStatus.LISTENING)

    # Manual activation (e.g., from hotkey)

    async def process_audio(self, audio_data, sample_rate: int = 16000) -> PipelineResult:
        """
        Manually process audio (e.g., from hotkey activation).

        Args:
            audio_data: Audio samples (numpy array)
            sample_rate: Sample rate of audio

        Returns:
            PipelineResult
        """
        import time

        # Create audio event
        event = AudioEvent(
            type="hotkey",
            audio_data=audio_data,
            timestamp=time.time(),
            duration_seconds=len(audio_data) / sample_rate,
        )

        return await self.pipeline.process_audio_event(event)

    # Status and control

    def set_status_callback(self, callback: Callable[[AssistantStatus], None]) -> None:
        """
        Set callback for status updates.

        Args:
            callback: Function to call when status changes
        """
        self._status_callback = callback

    def _update_status(self, new_status: AssistantStatus) -> None:
        """Update status and notify callback"""
        old_status = self._status
        self._status = new_status

        logger.info(f"Status: {old_status} -> {new_status}")

        if self._status_callback:
            try:
                self._status_callback(new_status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")

    async def _emit_event(self, event: Dict[str, Any]) -> None:
        """
        Emit event to UI (via stdout JSON protocol).

        Args:
            event: Event dictionary
        """
        try:
            event_json = json.dumps(event)
            print(f"EVENT: {event_json}", flush=True)
        except Exception as e:
            logger.error(f"Error emitting event: {e}")

    def get_status(self) -> AssistantStatus:
        """Get current status"""
        return self._status

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if self.metrics:
            return self.metrics.get_all_metrics()
        return {}

    def get_conversation_info(self) -> Dict[str, Any]:
        """Get conversation information"""
        if self.conversation_state:
            return self.conversation_state.get_session_info()
        return {}

    async def clear_conversation(self) -> None:
        """Clear conversation history"""
        if self.conversation_state:
            self.conversation_state.clear()
            logger.info("Conversation cleared")

    async def interrupt(self) -> None:
        """Interrupt current processing"""
        logger.info("Interrupt requested")

        if self.pipeline:
            await self.pipeline.interrupt()

        # Return to listening
        if self._running:
            self._update_status(AssistantStatus.LISTENING)

    def __repr__(self) -> str:
        return f"VoiceAssistant(status={self._status}, running={self._running})"
