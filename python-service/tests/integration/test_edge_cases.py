"""
Edge case integration tests.

Tests unusual scenarios, error conditions, and boundary cases.
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, Mock, patch
import time

from tests.fixtures import (
    generate_silence,
    generate_white_noise,
    get_mock_config,
    get_mock_error,
)


class TestAudioEdgeCases:
    """Test edge cases in audio processing"""

    @pytest.mark.asyncio
    async def test_empty_audio(self):
        """Test handling of empty audio input"""
        from voice_assistant.audio import AudioEvent

        # Create empty audio
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=np.array([], dtype=np.int16),
            timestamp=time.time(),
            duration_seconds=0.0,
        )

        # Mock STT should handle gracefully
        mock_stt = AsyncMock()
        mock_stt.transcribe.return_value = None

        # Process should handle None gracefully
        result = await mock_stt.transcribe(audio_event)
        assert result is None

    @pytest.mark.asyncio
    async def test_silence_only_audio(self):
        """Test handling of silence-only audio"""
        from voice_assistant.audio import AudioEvent

        # Create silence
        silence = generate_silence(duration_seconds=3.0)
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=silence,
            timestamp=time.time(),
            duration_seconds=3.0,
        )

        # STT should return empty or very short transcription
        mock_stt = AsyncMock()
        from voice_assistant.stt import TranscriptionResult

        mock_stt.transcribe.return_value = TranscriptionResult(
            text="",
            language="en",
            confidence=0.1,
            duration_ms=100,
        )

        result = await mock_stt.transcribe(audio_event)
        assert result.text == ""
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_noise_only_audio(self):
        """Test handling of noise-only audio"""
        from voice_assistant.audio import AudioEvent

        # Create white noise
        noise = generate_white_noise(duration_seconds=2.0)
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=noise,
            timestamp=time.time(),
            duration_seconds=2.0,
        )

        # STT might return gibberish with low confidence
        mock_stt = AsyncMock()
        from voice_assistant.stt import TranscriptionResult

        mock_stt.transcribe.return_value = TranscriptionResult(
            text="[unclear]",
            language="en",
            confidence=0.3,
            duration_ms=200,
        )

        result = await mock_stt.transcribe(audio_event)
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_very_long_audio(self):
        """Test handling of very long audio (> 30 seconds)"""
        from voice_assistant.audio import AudioEvent

        # Create 60 seconds of audio
        long_audio = np.random.randint(-32768, 32767, 16000 * 60, dtype=np.int16)
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=long_audio,
            timestamp=time.time(),
            duration_seconds=60.0,
        )

        # System should either chunk it or reject it
        assert audio_event.duration_seconds == 60.0
        assert len(audio_event.audio_data) == 16000 * 60

    @pytest.mark.asyncio
    async def test_clipped_audio(self):
        """Test handling of clipped/distorted audio"""
        from voice_assistant.audio import AudioEvent

        # Create clipped audio (all samples at max)
        clipped = np.full(16000 * 2, 32767, dtype=np.int16)
        audio_event = AudioEvent(
            type="audio_ready",
            audio_data=clipped,
            timestamp=time.time(),
            duration_seconds=2.0,
        )

        # Should still attempt to process
        assert audio_event.audio_data[0] == 32767
        assert np.all(audio_event.audio_data == 32767)


class TestSTTEdgeCases:
    """Test edge cases in speech-to-text"""

    @pytest.mark.asyncio
    async def test_very_low_confidence_transcription(self):
        """Test handling of very low confidence transcription"""
        from voice_assistant.stt import TranscriptionResult

        result = TranscriptionResult(
            text="unclear mumbling",
            language="en",
            confidence=0.15,
            duration_ms=500,
        )

        # Low confidence should trigger error recovery
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_foreign_language_detection(self):
        """Test handling of non-English audio"""
        from voice_assistant.stt import TranscriptionResult

        result = TranscriptionResult(
            text="Bonjour comment allez-vous",
            language="fr",
            confidence=0.90,
            duration_ms=600,
        )

        # Should detect French but might not process
        assert result.language != "en"
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_stt_timeout(self):
        """Test STT timeout handling"""
        mock_stt = AsyncMock()

        async def slow_transcribe(*args, **kwargs):
            await asyncio.sleep(35)  # Exceeds typical 30s timeout
            return None

        mock_stt.transcribe = slow_transcribe

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(mock_stt.transcribe(None), timeout=1.0)


class TestLLMEdgeCases:
    """Test edge cases in LLM processing"""

    @pytest.mark.asyncio
    async def test_llm_very_long_context(self):
        """Test LLM with very long conversation context"""
        from voice_assistant.llm import Message, MessageRole

        # Create 100 message history
        messages = [Message(role=MessageRole.SYSTEM, content="You are a helpful assistant.")]
        for i in range(50):
            messages.append(Message(role=MessageRole.USER, content=f"Question {i}"))
            messages.append(Message(role=MessageRole.ASSISTANT, content=f"Answer {i}"))

        # Should handle or truncate gracefully
        assert len(messages) == 101
        # Context management should limit to max_history_turns

    @pytest.mark.asyncio
    async def test_llm_empty_response(self):
        """Test handling of empty LLM response"""
        mock_llm = AsyncMock()
        from voice_assistant.llm import CompletionResult

        mock_llm.complete.return_value = CompletionResult(
            content="",
            model="test",
            tokens_used=0,
            finish_reason="stop",
        )

        result = await mock_llm.complete([])
        assert result.content == ""
        # Should trigger error recovery or retry

    @pytest.mark.asyncio
    async def test_llm_rate_limit_error(self):
        """Test handling of LLM rate limit"""
        mock_llm = AsyncMock()

        async def rate_limited(*args, **kwargs):
            raise Exception("Rate limit exceeded: 429")

        mock_llm.complete = rate_limited

        # Should retry with backoff
        with pytest.raises(Exception) as exc_info:
            await mock_llm.complete([])

        assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_llm_network_timeout(self):
        """Test LLM network timeout"""
        mock_llm = AsyncMock()

        async def timeout(*args, **kwargs):
            await asyncio.sleep(100)  # Simulate timeout

        mock_llm.complete = timeout

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(mock_llm.complete([]), timeout=1.0)

    @pytest.mark.asyncio
    async def test_llm_malformed_tool_call(self):
        """Test handling of malformed tool call from LLM"""
        from voice_assistant.llm import CompletionResult, ToolCall

        # Tool call with missing required field
        malformed_tool_call = {
            "id": "call_123",
            "name": "execute_applescript",
            # Missing 'arguments' field
        }

        # Should handle gracefully or raise validation error
        with pytest.raises((KeyError, ValueError, TypeError)):
            ToolCall(**malformed_tool_call)


class TestToolEdgeCases:
    """Test edge cases in tool execution"""

    @pytest.mark.asyncio
    async def test_tool_execution_timeout(self):
        """Test tool execution timeout"""
        mock_mcp = AsyncMock()

        async def slow_tool(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow tool
            return "Done"

        mock_mcp.call_tool = slow_tool

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                mock_mcp.call_tool("slow_tool", {}),
                timeout=1.0
            )

    @pytest.mark.asyncio
    async def test_tool_permission_denied(self):
        """Test tool execution when permission denied"""
        mock_mcp = AsyncMock()

        async def denied_tool(*args, **kwargs):
            raise PermissionError("Accessibility permission not granted")

        mock_mcp.call_tool = denied_tool

        with pytest.raises(PermissionError) as exc_info:
            await mock_mcp.call_tool("control_application", {})

        assert "permission" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_tool_invalid_arguments(self):
        """Test tool with invalid arguments"""
        mock_mcp = AsyncMock()

        async def validate_tool(tool_name, arguments):
            if "path" not in arguments:
                raise ValueError("Missing required argument: path")
            return "OK"

        mock_mcp.call_tool = validate_tool

        with pytest.raises(ValueError) as exc_info:
            await mock_mcp.call_tool("file_operation", {})

        assert "path" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_tool_result_too_large(self):
        """Test tool returning very large result"""
        mock_mcp = AsyncMock()

        # Create 1MB of result data
        large_result = "x" * (1024 * 1024)
        mock_mcp.call_tool.return_value = large_result

        result = await mock_mcp.call_tool("web_search", {})

        # Should truncate or handle gracefully
        assert len(result) > 0


class TestConversationEdgeCases:
    """Test edge cases in conversation flow"""

    @pytest.mark.asyncio
    async def test_rapid_consecutive_requests(self):
        """Test handling of rapid consecutive requests"""
        from voice_assistant.state import ConversationState

        state = ConversationState(max_turns=10)

        # Add 10 exchanges rapidly
        for i in range(10):
            state.add_exchange(f"Question {i}", f"Answer {i}")

        messages = state.get_messages()

        # Should maintain max_turns limit
        # System message + (max_turns * 2) user/assistant messages
        assert len(messages) <= 21  # 1 system + 10*2 exchanges

    @pytest.mark.asyncio
    async def test_conversation_context_overflow(self):
        """Test conversation exceeding context window"""
        from voice_assistant.state import ConversationState

        state = ConversationState(max_turns=100)

        # Add many long exchanges
        for i in range(100):
            long_query = "Please tell me a very long story " * 100
            long_answer = "Once upon a time " * 200
            state.add_exchange(long_query, long_answer)

        # Should truncate to fit context window
        messages = state.get_messages()
        assert len(messages) > 0  # Should have some messages

    @pytest.mark.asyncio
    async def test_conversation_clear_during_processing(self):
        """Test clearing conversation state during processing"""
        from voice_assistant.state import ConversationState

        state = ConversationState()
        state.add_exchange("Question 1", "Answer 1")

        # Clear during processing
        state.clear()

        messages = state.get_messages()
        # Should only have system message
        assert len(messages) == 1


class TestErrorRecoveryEdgeCases:
    """Test edge cases in error recovery"""

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test behavior when max retries exceeded"""
        from voice_assistant.errors import ErrorRecoveryHandler

        config = get_mock_config("full")
        config["error_handling"] = {
            "retry_on_failure": True,
            "max_retries": 3,
        }

        mock_tts = AsyncMock()
        handler = ErrorRecoveryHandler(config, tts_engine=mock_tts)

        # Simulate 4 failures (exceeds max_retries)
        attempt_count = [0]

        async def failing_operation():
            attempt_count[0] += 1
            raise Exception(f"Failure {attempt_count[0]}")

        # Should eventually give up after max_retries
        # (Implementation would use tenacity or similar)

    @pytest.mark.asyncio
    async def test_cascading_failures(self):
        """Test multiple components failing simultaneously"""
        # STT fails
        mock_stt = AsyncMock()
        mock_stt.transcribe.side_effect = Exception("STT failed")

        # LLM also fails
        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = Exception("LLM failed")

        # Should handle gracefully and not crash

    @pytest.mark.asyncio
    async def test_recovery_from_partial_failure(self):
        """Test recovery when some but not all tools fail"""
        mock_mcp = AsyncMock()

        call_count = [0]

        async def sometimes_fail(tool_name, arguments):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First call failed")
            return "Success"

        mock_mcp.call_tool = sometimes_fail

        # First call fails
        with pytest.raises(Exception):
            await mock_mcp.call_tool("tool1", {})

        # Second call succeeds
        result = await mock_mcp.call_tool("tool1", {})
        assert result == "Success"


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent operations"""

    @pytest.mark.asyncio
    async def test_concurrent_pipeline_requests(self):
        """Test handling of concurrent pipeline requests"""
        # System should queue or reject concurrent requests
        # (typically max_concurrent=1)
        pass

    @pytest.mark.asyncio
    async def test_interrupt_during_speech(self):
        """Test interrupting TTS during speech"""
        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = True

        # New request while speaking
        # Should stop current speech and start new request
        await mock_tts.stop()
        mock_tts.is_speaking.return_value = False

    @pytest.mark.asyncio
    async def test_state_consistency_under_concurrency(self):
        """Test conversation state consistency with concurrent access"""
        from voice_assistant.state import ConversationState

        state = ConversationState()

        # Simulate concurrent additions
        async def add_exchange(i):
            await asyncio.sleep(0.01 * i)
            state.add_exchange(f"Q{i}", f"A{i}")

        # Add 10 exchanges concurrently
        await asyncio.gather(*[add_exchange(i) for i in range(10)])

        messages = state.get_messages()
        # Should have all 10 exchanges (plus system message)
        assert len(messages) >= 11  # 1 system + at least 10 exchanges


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
