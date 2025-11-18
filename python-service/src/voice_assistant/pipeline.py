"""
Pipeline Coordination

Coordinates the flow from Audio → STT → LLM → MCP → TTS.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .audio import AudioEvent
from .stt import WhisperSTT, AudioInput, TranscriptionResult
from .llm import (
    LLMProvider,
    Message,
    MessageRole,
    CompletionResult,
    ToolDefinition,
    LLMError,
)
from .state import ConversationState
from .tts import MacOSTTS
from .metrics import MetricsCollector
from .errors import ErrorRecoveryHandler, ErrorType

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from pipeline execution"""
    success: bool
    transcription: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    tool_calls_made: int = 0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VoicePipeline:
    """
    Coordinates the voice assistant pipeline.

    Pipeline flow:
    1. Audio event → STT (Whisper)
    2. Transcription → LLM (with tools)
    3. If tool calls: Execute tools → Feed results back to LLM
    4. Final response → TTS (speak)

    Features:
    - Asynchronous pipeline execution
    - Tool calling support with multi-step execution
    - Error recovery at each stage
    - Performance metrics tracking
    - Streaming response support (future)
    """

    def __init__(
        self,
        stt: WhisperSTT,
        llm_provider: LLMProvider,
        tts: MacOSTTS,
        conversation_state: ConversationState,
        metrics: MetricsCollector,
        error_handler: ErrorRecoveryHandler,
        config: Dict[str, Any],
        mcp_client: Optional[Any] = None,
    ):
        """
        Initialize voice pipeline.

        Args:
            stt: Speech-to-text engine
            llm_provider: LLM provider for intelligence
            tts: Text-to-speech engine
            conversation_state: Conversation state manager
            metrics: Metrics collector
            error_handler: Error recovery handler
            config: Configuration dictionary
            mcp_client: Optional MCP client for tool execution
        """
        self.stt = stt
        self.llm = llm_provider
        self.tts = tts
        self.state = conversation_state
        self.metrics = metrics
        self.error_handler = error_handler
        self.config = config
        self.mcp_client = mcp_client

        # Pipeline configuration
        self.max_tool_iterations = config.get("conversation", {}).get(
            "max_tool_iterations", 5
        )

        logger.info("Voice pipeline initialized")

    async def process_audio_event(self, audio_event: AudioEvent) -> PipelineResult:
        """
        Process an audio event through the complete pipeline.

        Args:
            audio_event: Audio event with audio data

        Returns:
            PipelineResult with outcome
        """
        import time
        start_time = time.perf_counter()

        try:
            # Stage 1: Speech-to-Text
            transcription = await self._transcribe_audio(audio_event)

            if not transcription or not transcription.text:
                logger.warning("Empty transcription, aborting pipeline")
                return PipelineResult(
                    success=False,
                    error="No speech detected",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )

            logger.info(f"Transcription: {transcription.text}")

            # Stage 2: LLM Processing (with tool calling)
            response = await self._process_with_llm(transcription.text)

            if not response or not response.content:
                logger.warning("Empty LLM response")
                return PipelineResult(
                    success=False,
                    transcription=transcription.text,
                    error="No response generated",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )

            logger.info(f"Response: {response.content}")

            # Stage 3: Text-to-Speech
            await self._speak_response(response.content)

            # Record successful request
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.metrics.record_request(success=True, e2e_duration_ms=duration_ms)

            return PipelineResult(
                success=True,
                transcription=transcription.text,
                response=response.content,
                tool_calls_made=len(response.tool_calls) if response.tool_calls else 0,
                duration_ms=duration_ms,
                metadata={
                    "stt_duration_ms": transcription.duration_ms,
                    "stt_confidence": transcription.confidence,
                    "llm_model": response.model,
                    "llm_tokens": response.tokens_used,
                }
            )

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")

            duration_ms = (time.perf_counter() - start_time) * 1000
            self.metrics.record_request(success=False, e2e_duration_ms=duration_ms)

            # Handle error with recovery
            await self.error_handler.handle_generic_error(e, context="pipeline")

            return PipelineResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )

    async def _transcribe_audio(self, audio_event: AudioEvent) -> Optional[TranscriptionResult]:
        """
        Transcribe audio to text.

        Args:
            audio_event: Audio event with samples

        Returns:
            TranscriptionResult or None on error
        """
        with self.metrics.timer("stt"):
            try:
                audio_input = AudioInput(
                    samples=audio_event.audio_data,
                    sample_rate=16000,
                    language="en"
                )

                result = await self.stt.transcribe(audio_input)
                return result

            except Exception as e:
                logger.error(f"STT error: {e}")
                self.metrics.record_error("stt", e)
                await self.error_handler.handle_stt_error(e)
                return None

    async def _process_with_llm(self, user_message: str) -> Optional[CompletionResult]:
        """
        Process user message with LLM, including tool calling.

        Args:
            user_message: User's transcribed message

        Returns:
            CompletionResult or None on error
        """
        # Add user message to conversation
        self.state.add_user_message(user_message)

        # Get available tools if MCP is available
        tools = await self._get_available_tools() if self.mcp_client else None

        # Process with LLM (may involve multiple iterations for tool calling)
        result = await self._llm_with_tools(tools)

        if result:
            # Add assistant response to conversation
            tool_calls_dict = None
            if result.tool_calls:
                tool_calls_dict = [
                    {"name": tc.name, "arguments": tc.arguments}
                    for tc in result.tool_calls
                ]

            self.state.add_assistant_message(result.content, tool_calls_dict)

        return result

    async def _llm_with_tools(
        self,
        tools: Optional[List[ToolDefinition]]
    ) -> Optional[CompletionResult]:
        """
        Process LLM request with tool calling support.

        This handles the iterative loop:
        1. Send messages to LLM
        2. If tool calls: Execute tools
        3. Add tool results to messages
        4. Send back to LLM
        5. Repeat until no more tool calls or max iterations

        Args:
            tools: Available tools for the LLM

        Returns:
            Final CompletionResult
        """
        iteration = 0
        messages = self.state.get_messages()

        while iteration < self.max_tool_iterations:
            iteration += 1

            # Call LLM
            with self.metrics.timer("llm"):
                try:
                    result = await self.llm.complete(messages, tools=tools)
                except LLMError as e:
                    logger.error(f"LLM error: {e}")
                    self.metrics.record_error("llm", e)

                    # Try error recovery
                    recovery_action = await self.error_handler.handle_llm_error(e)

                    if recovery_action == "retry":
                        continue  # Retry same request
                    elif recovery_action == "fallback":
                        # TODO: Switch to fallback provider
                        return None
                    else:
                        return None

            # Check if LLM wants to call tools
            if not result.has_tool_calls:
                # No tool calls, return final response
                return result

            logger.info(f"LLM requested {len(result.tool_calls)} tool call(s)")

            # Execute tool calls
            for tool_call in result.tool_calls:
                tool_result = await self._execute_tool(
                    tool_call.name,
                    tool_call.arguments,
                    tool_call.id
                )

                # Add tool result to messages
                messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        content=tool_result,
                        name=tool_call.name,
                        tool_call_id=tool_call.id
                    )
                )

                # Also add to conversation state
                self.state.add_tool_message(
                    tool_call.name,
                    tool_result,
                    tool_call.id
                )

            # Continue loop to get LLM's response with tool results

        logger.warning(f"Reached max tool iterations ({self.max_tool_iterations})")
        return result  # Return last result

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_call_id: str
    ) -> str:
        """
        Execute a tool via MCP client.

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
            tool_call_id: Tool call ID for tracking

        Returns:
            Tool result as string
        """
        if not self.mcp_client:
            return "Error: Tool execution not available (MCP not initialized)"

        with self.metrics.timer(f"tool_{tool_name}"):
            try:
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                result = await self.mcp_client.call_tool(tool_name, tool_args)

                logger.info(f"Tool result: {str(result)[:200]}")
                return str(result)

            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                self.metrics.record_error(f"tool_{tool_name}", e)

                error_msg = await self.error_handler.handle_tool_error(
                    e, tool_name, tool_args
                )
                return error_msg

    async def _speak_response(self, response_text: str) -> None:
        """
        Speak the response using TTS.

        Args:
            response_text: Text to speak
        """
        with self.metrics.timer("tts"):
            try:
                await self.tts.speak(response_text, wait=True)
            except Exception as e:
                logger.error(f"TTS error: {e}")
                self.metrics.record_error("tts", e)
                await self.error_handler.handle_tts_error(e, response_text)

    async def _get_available_tools(self) -> Optional[List[ToolDefinition]]:
        """
        Get available tools from MCP server.

        Returns:
            List of tool definitions or None
        """
        if not self.mcp_client:
            return None

        try:
            tools = await self.mcp_client.list_tools()
            logger.info(f"Retrieved {len(tools)} tools from MCP server")
            return tools
        except Exception as e:
            logger.error(f"Error getting tools from MCP: {e}")
            return None

    async def interrupt(self) -> None:
        """Interrupt current pipeline execution"""
        logger.info("Pipeline interrupted")

        # Stop TTS if speaking
        if self.tts.is_speaking():
            await self.tts.stop()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status.

        Returns:
            Status dictionary
        """
        return {
            "stt_ready": self.stt is not None,
            "llm_ready": self.llm is not None,
            "tts_ready": self.tts is not None,
            "tts_speaking": self.tts.is_speaking() if self.tts else False,
            "mcp_available": self.mcp_client is not None,
            "conversation_turns": len(self.state._turns),
        }
