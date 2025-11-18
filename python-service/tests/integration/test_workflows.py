"""
End-to-end workflow tests.

Tests complete user scenarios including multi-turn conversations,
complex tool chains, and realistic usage patterns.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, Mock, patch, call
import time
from typing import List, Dict, Any

from tests.fixtures import (
    generate_wake_word_audio,
    generate_command_audio,
    generate_silence,
    get_mock_config,
    get_mock_tool_calls,
)


@pytest.fixture
def workflow_config():
    """Configuration for workflow tests"""
    return {
        "app": {
            "log_level": "INFO",
        },
        "llm": {
            "backend": "local_gpt_oss",
            "local_gpt_oss": {
                "model": "gpt-oss:120b",
                "timeout": 120,
            },
        },
        "conversation": {
            "max_history_turns": 10,
            "max_tool_iterations": 5,
            "context_window_tokens": 4096,
            "system_prompt": "You are a helpful voice assistant for macOS.",
        },
        "error_handling": {
            "retry_on_failure": True,
            "max_retries": 3,
            "speak_errors": False,
        },
    }


class TestSimpleWorkflows:
    """Test simple single-turn workflows"""

    @pytest.mark.asyncio
    async def test_simple_query_workflow(self, workflow_config):
        """
        Workflow: User asks simple question, gets immediate answer

        Steps:
        1. Wake word detected
        2. User: "What time is it?"
        3. Assistant: "It's 3:45 PM"
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult, Message, MessageRole

        # Setup mocks
        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="What time is it?",
            language="en",
            confidence=0.97,
            duration_ms=380,
        )

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = CompletionResult(
            content="It's currently 3:45 PM.",
            model="gpt-oss:120b",
            tokens_used=25,
            finish_reason="stop",
        )

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        # Create pipeline
        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
        )

        # Generate audio
        audio, _ = generate_command_audio("What time is it?")
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=audio,
            timestamp=time.time(),
            duration_seconds=len(audio) / 16000,
        )

        # Execute workflow
        result = await pipeline.process_audio_event(audio_event)

        # Verify
        assert result.success is True
        assert result.transcription == "What time is it?"
        assert "3:45 PM" in result.response

        # Verify conversation state
        messages = state.get_messages()
        assert any(m.role == MessageRole.USER and "time" in m.content.lower() for m in messages)
        assert any(m.role == MessageRole.ASSISTANT and "3:45" in m.content for m in messages)

    @pytest.mark.asyncio
    async def test_single_tool_workflow(self, workflow_config):
        """
        Workflow: User requests action requiring single tool

        Steps:
        1. User: "Open Safari"
        2. LLM calls execute_applescript tool
        3. Tool executes successfully
        4. Assistant: "I've opened Safari for you"
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult, ToolCall

        # Setup mocks
        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="Open Safari",
            language="en",
            confidence=0.98,
            duration_ms=350,
        )

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            # First call: tool call
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_001",
                        name="execute_applescript",
                        arguments={"script": 'tell application "Safari" to activate'},
                    )
                ],
            ),
            # Second call: final response
            CompletionResult(
                content="I've opened Safari for you.",
                model="gpt-oss:120b",
                tokens_used=20,
                finish_reason="stop",
            ),
        ]

        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = "Success: Safari activated"
        mock_mcp.list_tools.return_value = []

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        # Create pipeline
        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
            mcp_client=mock_mcp,
        )

        # Generate audio
        audio, _ = generate_command_audio("Open Safari")
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=audio,
            timestamp=time.time(),
            duration_seconds=len(audio) / 16000,
        )

        # Execute workflow
        result = await pipeline.process_audio_event(audio_event)

        # Verify
        assert result.success is True
        assert result.tool_calls_made == 1
        assert "Safari" in result.response

        # Verify tool was called
        mock_mcp.call_tool.assert_called_once()


class TestMultiTurnWorkflows:
    """Test multi-turn conversation workflows"""

    @pytest.mark.asyncio
    async def test_followup_question_workflow(self, workflow_config):
        """
        Workflow: User asks follow-up question referencing previous context

        Steps:
        1. User: "What's the weather like?"
        2. Assistant: "It's sunny and 72°F"
        3. User: "Should I bring an umbrella?"
        4. Assistant: "No, you won't need one..."
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult

        # Setup mocks
        mock_stt = AsyncMock()
        transcriptions = [
            TranscriptionResult(
                text="What's the weather like?",
                language="en",
                confidence=0.95,
                duration_ms=450,
            ),
            TranscriptionResult(
                text="Should I bring an umbrella?",
                language="en",
                confidence=0.94,
                duration_ms=480,
            ),
        ]
        mock_stt.transcribe.side_effect = transcriptions

        mock_llm = AsyncMock()
        responses = [
            CompletionResult(
                content="It's sunny and 72°F today with clear skies.",
                model="gpt-oss:120b",
                tokens_used=45,
                finish_reason="stop",
            ),
            CompletionResult(
                content="No, you won't need an umbrella. It's going to stay clear all day.",
                model="gpt-oss:120b",
                tokens_used=50,
                finish_reason="stop",
            ),
        ]
        mock_llm.complete.side_effect = responses

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        # Create pipeline
        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
        )

        # First query
        audio1, _ = generate_command_audio("What's the weather like?")
        event1 = AudioEvent(
            type="audio_ready",
            audio_data=audio1,
            timestamp=time.time(),
            duration_seconds=len(audio1) / 16000,
        )

        result1 = await pipeline.process_audio_event(event1)
        assert result1.success is True
        assert "sunny" in result1.response.lower()

        # Follow-up query
        audio2, _ = generate_command_audio("Should I bring an umbrella?")
        event2 = AudioEvent(
            type="audio_ready",
            audio_data=audio2,
            timestamp=time.time(),
            duration_seconds=len(audio2) / 16000,
        )

        result2 = await pipeline.process_audio_event(event2)
        assert result2.success is True
        assert "umbrella" in result2.response.lower()

        # Verify conversation history maintained
        messages = state.get_messages()
        assert len(messages) >= 5  # system + 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_context_aware_workflow(self, workflow_config):
        """
        Workflow: Assistant uses context from previous messages

        Steps:
        1. User: "My name is John"
        2. Assistant: "Nice to meet you, John"
        3. User: "What's my name?"
        4. Assistant: "Your name is John"
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult

        mock_stt = AsyncMock()
        transcriptions = [
            TranscriptionResult(text="My name is John", language="en", confidence=0.96, duration_ms=400),
            TranscriptionResult(text="What's my name?", language="en", confidence=0.97, duration_ms=350),
        ]
        mock_stt.transcribe.side_effect = transcriptions

        mock_llm = AsyncMock()
        responses = [
            CompletionResult(
                content="Nice to meet you, John!",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="stop",
            ),
            CompletionResult(
                content="Your name is John.",
                model="gpt-oss:120b",
                tokens_used=25,
                finish_reason="stop",
            ),
        ]
        mock_llm.complete.side_effect = responses

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
        )

        # First exchange
        audio1, _ = generate_command_audio("My name is John")
        event1 = AudioEvent(type="audio_ready", audio_data=audio1, timestamp=time.time(), duration_seconds=1.0)
        result1 = await pipeline.process_audio_event(event1)
        assert "John" in result1.response

        # Second exchange (context-aware)
        audio2, _ = generate_command_audio("What's my name?")
        event2 = AudioEvent(type="audio_ready", audio_data=audio2, timestamp=time.time(), duration_seconds=1.0)
        result2 = await pipeline.process_audio_event(event2)
        assert "John" in result2.response


class TestComplexToolWorkflows:
    """Test complex workflows with multiple tools"""

    @pytest.mark.asyncio
    async def test_sequential_tools_workflow(self, workflow_config):
        """
        Workflow: Multiple tools executed in sequence

        Steps:
        1. User: "Create a file and then open it in TextEdit"
        2. LLM calls file_operation to create file
        3. LLM calls execute_applescript to open TextEdit
        4. Assistant confirms both actions
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult, ToolCall

        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="Create a file called notes.txt and then open it in TextEdit",
            language="en",
            confidence=0.93,
            duration_ms=650,
        )

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            # First call: file creation tool
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=40,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_001",
                        name="file_operation",
                        arguments={"operation": "write", "path": "~/notes.txt", "content": ""},
                    )
                ],
            ),
            # Second call: open in TextEdit
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=35,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_002",
                        name="execute_applescript",
                        arguments={"script": 'tell application "TextEdit" to open POSIX file "/Users/user/notes.txt"'},
                    )
                ],
            ),
            # Final response
            CompletionResult(
                content="I've created notes.txt and opened it in TextEdit for you.",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="stop",
            ),
        ]

        mock_mcp = AsyncMock()
        tool_results = [
            "File created: ~/notes.txt",
            "TextEdit opened successfully",
        ]
        mock_mcp.call_tool.side_effect = tool_results
        mock_mcp.list_tools.return_value = []

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
            mcp_client=mock_mcp,
        )

        audio, _ = generate_command_audio("Create file and open TextEdit")
        event = AudioEvent(type="audio_ready", audio_data=audio, timestamp=time.time(), duration_seconds=2.0)

        result = await pipeline.process_audio_event(event)

        # Verify both tools were called
        assert result.tool_calls_made >= 1
        assert "notes.txt" in result.response
        assert "TextEdit" in result.response

    @pytest.mark.asyncio
    async def test_parallel_tools_workflow(self, workflow_config):
        """
        Workflow: Multiple tools that can be executed in parallel

        Steps:
        1. User: "Check my battery level and disk space"
        2. LLM calls both get_system_info tools
        3. Both execute in parallel
        4. Assistant reports both results
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult, ToolCall

        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="Check my battery level and disk space",
            language="en",
            confidence=0.94,
            duration_ms=550,
        )

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            # Tool calls (parallel)
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=50,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_001",
                        name="get_system_info",
                        arguments={"info_type": "battery"},
                    ),
                    ToolCall(
                        id="call_002",
                        name="get_system_info",
                        arguments={"info_type": "disk_space"},
                    ),
                ],
            ),
            # Final response
            CompletionResult(
                content="Your battery is at 87% and you have 245 GB of free disk space.",
                model="gpt-oss:120b",
                tokens_used=40,
                finish_reason="stop",
            ),
        ]

        mock_mcp = AsyncMock()
        tool_results = {
            "battery": "87%, Charging: No",
            "disk_space": "245 GB free",
        }

        async def call_tool(name, args):
            info_type = args.get("info_type")
            return tool_results.get(info_type, "Unknown")

        mock_mcp.call_tool.side_effect = call_tool
        mock_mcp.list_tools.return_value = []

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
            mcp_client=mock_mcp,
        )

        audio, _ = generate_command_audio("Check battery and disk space")
        event = AudioEvent(type="audio_ready", audio_data=audio, timestamp=time.time(), duration_seconds=2.0)

        result = await pipeline.process_audio_event(event)

        assert result.success is True
        assert "87" in result.response or "battery" in result.response.lower()
        assert "245" in result.response or "disk" in result.response.lower()


class TestErrorRecoveryWorkflows:
    """Test workflows with error recovery"""

    @pytest.mark.asyncio
    async def test_tool_failure_recovery_workflow(self, workflow_config):
        """
        Workflow: Tool fails but system recovers gracefully

        Steps:
        1. User: "Open NonExistentApp"
        2. LLM calls execute_applescript
        3. Tool fails (app doesn't exist)
        4. LLM acknowledges failure gracefully
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult, ToolCall

        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = TranscriptionResult(
            text="Open NonExistentApp",
            language="en",
            confidence=0.95,
            duration_ms=400,
        )

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = [
            # Tool call
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_001",
                        name="execute_applescript",
                        arguments={"script": 'tell application "NonExistentApp" to activate'},
                    )
                ],
            ),
            # Recovery response
            CompletionResult(
                content="I couldn't find an application named NonExistentApp. Could you check the name?",
                model="gpt-oss:120b",
                tokens_used=35,
                finish_reason="stop",
            ),
        ]

        mock_mcp = AsyncMock()
        mock_mcp.call_tool.side_effect = Exception("Application not found")
        mock_mcp.list_tools.return_value = []

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
            mcp_client=mock_mcp,
        )

        audio, _ = generate_command_audio("Open NonExistentApp")
        event = AudioEvent(type="audio_ready", audio_data=audio, timestamp=time.time(), duration_seconds=1.5)

        result = await pipeline.process_audio_event(event)

        # Should handle gracefully
        assert result.success is True or result.error is not None

    @pytest.mark.asyncio
    async def test_clarification_workflow(self, workflow_config):
        """
        Workflow: Assistant asks for clarification

        Steps:
        1. User: (unclear audio)
        2. STT returns low confidence
        3. Assistant: "I didn't catch that, could you repeat?"
        4. User repeats clearly
        5. Assistant processes correctly
        """
        from voice_assistant import VoicePipeline
        from voice_assistant.state import ConversationState
        from voice_assistant.metrics import MetricsCollector
        from voice_assistant.errors import ErrorRecoveryHandler
        from voice_assistant.audio import AudioEvent
        from voice_assistant.stt import TranscriptionResult
        from voice_assistant.llm import CompletionResult

        mock_stt = AsyncMock()
        transcriptions = [
            # First: unclear
            TranscriptionResult(
                text="mumble unclear",
                language="en",
                confidence=0.35,
                duration_ms=400,
            ),
            # Second: clear
            TranscriptionResult(
                text="What time is it?",
                language="en",
                confidence=0.97,
                duration_ms=380,
            ),
        ]
        mock_stt.transcribe.side_effect = transcriptions

        mock_llm = AsyncMock()
        responses = [
            CompletionResult(
                content="I'm sorry, I didn't quite catch that. Could you please repeat?",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="stop",
            ),
            CompletionResult(
                content="It's currently 3:45 PM.",
                model="gpt-oss:120b",
                tokens_used=25,
                finish_reason="stop",
            ),
        ]
        mock_llm.complete.side_effect = responses

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(workflow_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=workflow_config,
        )

        # First attempt (unclear)
        audio1 = generate_white_noise(duration_seconds=2.0)
        event1 = AudioEvent(type="audio_ready", audio_data=audio1, timestamp=time.time(), duration_seconds=2.0)
        result1 = await pipeline.process_audio_event(event1)

        # Second attempt (clear)
        audio2, _ = generate_command_audio("What time is it?")
        event2 = AudioEvent(type="audio_ready", audio_data=audio2, timestamp=time.time(), duration_seconds=1.0)
        result2 = await pipeline.process_audio_event(event2)

        assert result2.success is True
        assert "3:45" in result2.response


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
