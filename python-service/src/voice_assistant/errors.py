"""
Error Recovery and Handling

Provides error recovery strategies for each pipeline stage.
"""

import logging
from typing import Optional, Callable, Any, Dict
from enum import Enum
import asyncio

from .llm import LLMError, LLMConnectionError, LLMTimeoutError, LLMRateLimitError

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Types of errors in the pipeline"""
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TOOL_ERROR = "tool_error"
    NETWORK_ERROR = "network_error"
    AUDIO_ERROR = "audio_error"
    TTS_ERROR = "tts_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(str, Enum):
    """Actions to take on error"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    ASK_USER = "ask_user"


class VoiceAssistantError(Exception):
    """Base exception for voice assistant errors"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        recoverable: bool = True,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.recoverable = recoverable
        self.original_error = original_error


class ErrorRecoveryHandler:
    """
    Handles error recovery for different pipeline stages.

    Features:
    - Stage-specific error handlers
    - Retry logic with exponential backoff
    - Fallback strategies
    - User-facing error messages
    - Error logging and metrics
    """

    def __init__(
        self,
        config: Dict[str, Any],
        tts_engine: Optional[Any] = None,
        fallback_provider: Optional[Any] = None,
    ):
        """
        Initialize error recovery handler.

        Args:
            config: Error handling configuration
            tts_engine: TTS engine for speaking error messages
            fallback_provider: Fallback LLM provider for when primary fails
        """
        self.config = config
        self.tts = tts_engine
        self.fallback_provider = fallback_provider

        # Extract error handling config
        error_config = config.get("error_handling", {})
        self.retry_on_failure = error_config.get("retry_on_failure", True)
        self.max_retries = error_config.get("max_retries", 3)
        self.speak_errors = error_config.get("speak_errors", True)
        self.error_phrases = error_config.get("error_phrases", {})
        self.use_fallback = error_config.get("fallback", {}).get(
            "use_cloud_api_on_local_failure", False
        )

        # Retry configuration
        retry_config = config.get("llm", {}).get("retry", {})
        self.retry_initial_delay = retry_config.get("initial_delay", 1.0)
        self.retry_max_delay = retry_config.get("max_delay", 10.0)
        self.retry_exponential_base = retry_config.get("exponential_base", 2)

        logger.info("Error recovery handler initialized")

    async def handle_stt_error(self, error: Exception) -> str:
        """
        Handle STT (speech-to-text) errors.

        Strategy: Ask user to repeat, as STT errors are usually audio quality issues.

        Args:
            error: The STT error

        Returns:
            Recovery action result
        """
        logger.error(f"STT error: {error}")

        message = self.error_phrases.get(
            "stt_error",
            "Sorry, I didn't catch that. Could you repeat?"
        )

        if self.speak_errors and self.tts:
            await self.tts.speak(message)

        return "repeat_request"

    async def handle_llm_error(self, error: Exception, retry_count: int = 0) -> str:
        """
        Handle LLM errors.

        Strategy:
        1. Retry with exponential backoff (for transient errors)
        2. Try fallback provider if configured
        3. Apologize to user if all else fails

        Args:
            error: The LLM error
            retry_count: Current retry attempt

        Returns:
            Recovery action result
        """
        logger.error(f"LLM error (attempt {retry_count + 1}): {error}")

        # Determine if error is retryable
        is_retryable = isinstance(error, (LLMConnectionError, LLMTimeoutError))

        if is_retryable and retry_count < self.max_retries and self.retry_on_failure:
            # Calculate backoff delay
            delay = min(
                self.retry_initial_delay * (self.retry_exponential_base ** retry_count),
                self.retry_max_delay
            )
            logger.info(f"Retrying LLM request in {delay:.1f}s...")
            await asyncio.sleep(delay)
            return "retry"

        # Try fallback provider if available
        if self.use_fallback and self.fallback_provider:
            logger.info("Attempting fallback LLM provider")
            return "fallback"

        # All recovery attempts failed
        message = self.error_phrases.get(
            "llm_error",
            "I'm having trouble processing that right now."
        )

        if self.speak_errors and self.tts:
            await self.tts.speak(message)

        return "error"

    async def handle_tool_error(
        self,
        error: Exception,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> str:
        """
        Handle tool execution errors.

        Strategy: Return error message to LLM so it can decide what to do.

        Args:
            error: The tool error
            tool_name: Name of the tool that failed
            tool_args: Arguments passed to the tool

        Returns:
            Error message for LLM
        """
        logger.error(f"Tool error ({tool_name}): {error}")
        logger.debug(f"Tool arguments: {tool_args}")

        error_msg = (
            f"Tool '{tool_name}' failed with error: {str(error)}. "
            f"The tool was called with arguments: {tool_args}"
        )

        return error_msg

    async def handle_network_error(self, error: Exception) -> str:
        """
        Handle network connectivity errors.

        Strategy: Inform user of connectivity issue.

        Args:
            error: The network error

        Returns:
            Recovery action result
        """
        logger.error(f"Network error: {error}")

        message = self.error_phrases.get(
            "network_error",
            "I'm having trouble connecting. Please check your internet."
        )

        if self.speak_errors and self.tts:
            await self.tts.speak(message)

        return "network_error"

    async def handle_audio_error(self, error: Exception) -> str:
        """
        Handle audio pipeline errors.

        Strategy: Check permissions, device availability.

        Args:
            error: The audio error

        Returns:
            Recovery action result
        """
        logger.error(f"Audio error: {error}")

        # Check if it's a permission error
        error_str = str(error).lower()
        if "permission" in error_str or "access" in error_str:
            message = "I don't have permission to access the microphone. Please grant access in System Settings."
        else:
            message = "I'm having trouble with audio input. Please check your microphone."

        if self.speak_errors and self.tts:
            await self.tts.speak(message)

        return "audio_error"

    async def handle_tts_error(self, error: Exception, text: str) -> str:
        """
        Handle TTS (text-to-speech) errors.

        Strategy: Log the text that couldn't be spoken.

        Args:
            error: The TTS error
            text: Text that failed to be spoken

        Returns:
            Recovery action result
        """
        logger.error(f"TTS error: {error}")
        logger.info(f"Failed to speak: {text}")

        # TTS errors are non-critical - continue without speaking
        return "skip_tts"

    async def handle_generic_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> str:
        """
        Handle generic/unknown errors.

        Args:
            error: The error
            context: Optional context about where error occurred

        Returns:
            Recovery action result
        """
        context_msg = f" during {context}" if context else ""
        logger.exception(f"Unexpected error{context_msg}: {error}")

        message = "I encountered an unexpected error. Please try again."

        if self.speak_errors and self.tts:
            await self.tts.speak(message)

        return "unknown_error"

    async def with_retry(
        self,
        func: Callable,
        *args,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            error_type: Type of error being handled
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e

                if attempt < self.max_retries:
                    delay = min(
                        self.retry_initial_delay * (self.retry_exponential_base ** attempt),
                        self.retry_max_delay
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")

        # All retries exhausted
        raise last_error

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should be retried.

        Args:
            error: The error to check

        Returns:
            True if error should be retried
        """
        # Retry on network/timeout errors
        if isinstance(error, (LLMConnectionError, LLMTimeoutError, LLMRateLimitError)):
            return True

        # Don't retry invalid requests
        if isinstance(error, LLMError):
            return False

        # Retry other exceptions
        return True

    def get_user_message(self, error_type: ErrorType) -> str:
        """
        Get user-facing error message for error type.

        Args:
            error_type: Type of error

        Returns:
            User-friendly error message
        """
        return self.error_phrases.get(
            error_type.value,
            "I encountered an error. Please try again."
        )
