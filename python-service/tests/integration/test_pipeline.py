"""
Integration tests for the complete voice assistant pipeline.

Tests the full flow: Audio → STT → LLM → MCP → TTS
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import time

from voice_assistant import (
    VoiceAssistant,
    AssistantStatus,
    VoicePipeline,
    PipelineResult,
)
from voice_assistant.audio import AudioEvent
from voice_assistant.stt import AudioInput, TranscriptionResult, Segment
from voice_assistant.llm import Message, MessageRole, CompletionResult


@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "app": {
            "version": "1.0.0",
            "log_level": "INFO",
            "log_dir": "/tmp/voice-assistant/logs",
        },
        "llm": {
            "backend": "local_gpt_oss",
            "local_gpt_oss": {
                "base_url": "http://localhost:8080",
                "model": "gpt-oss:120b",
                "timeout": 120,
                "max_tokens": 1024,
                "temperature": 0.7,
            },
        },
        "audio": {
            "input": {
                "sample_rate": 16000,
                "channels": 1,
            },
        },
        "stt": {
            "whisper": {
                "model": "small.en",
                "language": "en",
            },
        },
        "tts": {
            "engine": "macos_native",
            "macos": {
                "voice": "Samantha",
                "rate": 200,
            },
        },
        "conversation": {
            "max_history_turns": 10,
            "context_window_tokens": 4096,
            "system_prompt": "You are a helpful assistant.",
        },
        "performance": {
            "enable_metrics": True,
            "metrics_log_interval_seconds": 60,
        },
        "error_handling": {
            "retry_on_failure": True,
            "max_retries": 3,
            "speak_errors": False,  # Don't speak errors in tests
        },
    }


@pytest.fixture
def mock_audio_event():
    """Create mock audio event"""
    # Generate 2 seconds of dummy audio (16kHz, mono)
    duration = 2.0
    sample_rate = 16000
    num_samples = int(duration * sample_rate)
    audio_data = np.random.randint(-32768, 32767, num_samples, dtype=np.int16)

    return AudioEvent(
        type="audio_ready",
        audio_data=audio_data,
        timestamp=time.time(),
        duration_seconds=duration,
    )


class TestPipelineIntegration:
    """Test complete pipeline integration"""

    @pytest.mark.asyncio
    async def test_pipeline_with_mocked_components(self, test_config, mock_audio_event):
        """Test pipeline with mocked STT, LLM, and TTS"""

        # Mock STT
        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="What is the weather like today?",
            language="en",
            confidence=0.95,
            duration_ms=450,
        )

        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = CompletionResult(
            content="The weather is sunny and warm today.",
            model="gpt-oss:120b",
            tokens_used=50,
            finish_reason="stop",
        )

        # Mock TTS
        mock_tts = AsyncMock()
        mock_tts.speak.return_value = None
        mock_tts.is_speaking.return_value = False

        # Create pipeline with mocked components
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler

        state = ConversationState(max_turns=10)
        metrics = MetricsCollector(enable_metrics=True)
        error_handler = ErrorRecoveryHandler(test_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=test_config,
        )

        # Process audio event
        result = await pipeline.process_audio_event(mock_audio_event)

        # Verify result
        assert result.success is True
        assert result.transcription == "What is the weather like today?"
        assert result.response == "The weather is sunny and warm today."
        assert result.error is None
        assert result.duration_ms > 0

        # Verify components were called
        mock_stt.transcribe.assert_called_once()
        mock_llm.complete.assert_called_once()
        mock_tts.speak.assert_called_once_with(
            "The weather is sunny and warm today.",
            wait=True
        )

        # Verify conversation state
        messages = state.get_messages()
        assert len(messages) == 3  # system + user + assistant
        assert messages[1].role == MessageRole.USER
        assert messages[1].content == "What is the weather like today?"
        assert messages[2].role == MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_pipeline_with_tool_calls(self, test_config, mock_audio_event):
        """Test pipeline with LLM tool calling"""

        # Mock STT
        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="Open Safari",
            language="en",
            confidence=0.95,
            duration_ms=400,
        )

        # Mock LLM - first call returns tool call, second call returns final response
        from voice_assistant.llm import ToolCall

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            # First call: LLM wants to call a tool
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="execute_applescript",
                        arguments={"script": 'tell application "Safari" to activate'},
                    )
                ],
            ),
            # Second call: LLM responds with final answer
            CompletionResult(
                content="I've opened Safari for you.",
                model="gpt-oss:120b",
                tokens_used=20,
                finish_reason="stop",
            ),
        ]

        # Mock MCP client
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = "Success: Safari opened"
        mock_mcp.list_tools.return_value = []

        # Mock TTS
        mock_tts = AsyncMock()

        # Create pipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(test_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=test_config,
            mcp_client=mock_mcp,
        )

        # Process audio event
        result = await pipeline.process_audio_event(mock_audio_event)

        # Verify result
        assert result.success is True
        assert result.response == "I've opened Safari for you."
        assert result.tool_calls_made == 1

        # Verify tool was called
        mock_mcp.call_tool.assert_called_once_with(
            "execute_applescript",
            {"script": 'tell application "Safari" to activate'},
        )

        # Verify LLM was called twice (once for tool call, once for final response)
        assert mock_llm.complete.call_count == 2

    @pytest.mark.asyncio
    async def test_pipeline_error_recovery(self, test_config, mock_audio_event):
        """Test pipeline error recovery"""

        # Mock STT that fails
        mock_stt = AsyncMock()
        mock_stt.transcribe.side_effect = Exception("STT failed")

        # Mock TTS
        mock_tts = AsyncMock()

        # Create minimal pipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(test_config, tts_engine=mock_tts)

        mock_llm = AsyncMock()

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=test_config,
        )

        # Process audio event
        result = await pipeline.process_audio_event(mock_audio_event)

        # Verify error was handled
        assert result.success is False
        assert result.error is not None

        # Verify metrics recorded error
        metrics_data = metrics.get_all_metrics()
        assert metrics_data["system"]["failed_requests"] > 0


class TestVoiceAssistantOrchestrator:
    """Test VoiceAssistant orchestrator"""

    @pytest.mark.asyncio
    async def test_assistant_initialization(self, test_config):
        """Test that assistant initializes successfully"""

        with patch('voice_assistant.orchestrator.AudioPipeline'), \
             patch('voice_assistant.orchestrator.WhisperSTT'), \
             patch('voice_assistant.orchestrator.ProviderFactory'), \
             patch('voice_assistant.orchestrator.MacOSTTS'):

            assistant = VoiceAssistant(test_config)

            # Initialize
            success = await assistant.initialize()

            assert success is True
            assert assistant.get_status() == AssistantStatus.IDLE
            assert assistant.metrics is not None
            assert assistant.conversation_state is not None

            # Cleanup
            await assistant.cleanup()

    @pytest.mark.asyncio
    async def test_assistant_status_transitions(self, test_config):
        """Test status transitions"""

        with patch('voice_assistant.orchestrator.AudioPipeline'), \
             patch('voice_assistant.orchestrator.WhisperSTT'), \
             patch('voice_assistant.orchestrator.ProviderFactory'), \
             patch('voice_assistant.orchestrator.MacOSTTS'):

            assistant = VoiceAssistant(test_config)
            await assistant.initialize()

            # Track status changes
            statuses = []

            def status_callback(status):
                statuses.append(status)

            assistant.set_status_callback(status_callback)

            # Start assistant
            await assistant.start()
            assert AssistantStatus.LISTENING in statuses

            # Stop assistant
            await assistant.stop()
            assert AssistantStatus.STOPPED in statuses

            # Cleanup
            await assistant.cleanup()


@pytest.mark.asyncio
async def test_end_to_end_latency(test_config, mock_audio_event):
    """Test end-to-end latency is within acceptable range"""

    # Mock components with realistic delays
    mock_stt = AsyncMock()

    async def stt_transcribe(*args, **kwargs):
        await asyncio.sleep(0.4)  # 400ms STT
        return TranscriptionResult(
            text="Test query",
            language="en",
            confidence=0.9,
            duration_ms=400,
        )

    mock_stt.transcribe = stt_transcribe

    mock_llm = AsyncMock()

    async def llm_complete(*args, **kwargs):
        await asyncio.sleep(1.5)  # 1500ms LLM
        return CompletionResult(
            content="Test response",
            model="test",
            tokens_used=50,
            finish_reason="stop",
        )

    mock_llm.complete = llm_complete

    mock_tts = AsyncMock()

    async def tts_speak(*args, **kwargs):
        await asyncio.sleep(0.5)  # 500ms TTS
        return None

    mock_tts.speak = tts_speak
    mock_tts.is_speaking.return_value = False

    # Create pipeline
    from voice_assistant.state import ConversationState
    from voice_assistant.metrics import MetricsCollector
    from voice_assistant.errors import ErrorRecoveryHandler

    state = ConversationState()
    metrics = MetricsCollector()
    error_handler = ErrorRecoveryHandler(test_config, tts_engine=mock_tts)

    pipeline = VoicePipeline(
        stt=mock_stt,
        llm_provider=mock_llm,
        tts=mock_tts,
        conversation_state=state,
        metrics=metrics,
        error_handler=error_handler,
        config=test_config,
    )

    # Process and measure latency
    start = time.perf_counter()
    result = await pipeline.process_audio_event(mock_audio_event)
    end = time.perf_counter()

    actual_duration = (end - start) * 1000  # Convert to ms

    # Verify result
    assert result.success is True

    # Verify latency (should be ~2400ms: 400 + 1500 + 500)
    # Allow some overhead
    assert 2000 < actual_duration < 3000, f"Latency {actual_duration}ms outside expected range"

    print(f"End-to-end latency: {actual_duration:.1f}ms")
    print(f"Reported duration: {result.duration_ms:.1f}ms")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
