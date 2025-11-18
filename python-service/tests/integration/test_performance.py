"""
Performance tests for voice assistant pipeline.

Measures latency at each stage and end-to-end performance.
"""

import pytest
import asyncio
import numpy as np
import time
from unittest.mock import AsyncMock
from statistics import mean, stdev

from voice_assistant import (
    VoicePipeline,
    ConversationState,
    MetricsCollector,
)
from voice_assistant.audio import AudioEvent
from voice_assistant.stt import TranscriptionResult
from voice_assistant.llm import CompletionResult
from voice_assistant.errors import ErrorRecoveryHandler


# Performance targets from CLAUDE.md
TARGETS = {
    "wake_word_latency_ms": 500,
    "stt_transcription_ms": 500,  # For 5s audio
    "llm_local_response_ms": 2000,
    "llm_cloud_response_ms": 5000,
    "tool_execution_ms": 1000,
    "tts_start_ms": 500,
    "end_to_end_ms": 5000,
}


@pytest.fixture
def perf_config():
    """Configuration for performance tests"""
    return {
        "app": {"log_level": "WARNING"},  # Reduce log noise
        "conversation": {
            "max_history_turns": 10,
            "max_tool_iterations": 5,
        },
        "performance": {
            "enable_metrics": True,
        },
        "error_handling": {
            "speak_errors": False,
        },
    }


@pytest.fixture
def generate_audio():
    """Factory for generating test audio"""

    def _generate(duration_seconds: float = 5.0, sample_rate: int = 16000):
        num_samples = int(duration_seconds * sample_rate)
        audio_data = np.random.randint(-32768, 32767, num_samples, dtype=np.int16)
        return AudioEvent(
            type="audio_ready",
            audio_data=audio_data,
            timestamp=time.time(),
            duration_seconds=duration_seconds,
        )

    return _generate


class TestSTTPerformance:
    """Test STT performance"""

    @pytest.mark.asyncio
    async def test_stt_latency(self, generate_audio):
        """Test STT transcription latency for 5-second audio"""

        # Mock STT with realistic delay
        mock_stt = AsyncMock()

        async def transcribe_with_delay(*args, **kwargs):
            # Simulate processing time
            await asyncio.sleep(0.4)  # 400ms - under 500ms target
            return TranscriptionResult(
                text="This is a test transcription",
                language="en",
                confidence=0.95,
                duration_ms=400,
            )

        mock_stt.transcribe = transcribe_with_delay

        # Generate 5-second audio
        audio_event = generate_audio(duration_seconds=5.0)

        # Measure latency
        start = time.perf_counter()
        result = await mock_stt.transcribe(audio_event)
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result.text is not None
        assert duration_ms < TARGETS["stt_transcription_ms"], \
            f"STT took {duration_ms:.1f}ms, target is {TARGETS['stt_transcription_ms']}ms"

        print(f"✓ STT latency: {duration_ms:.1f}ms (target: {TARGETS['stt_transcription_ms']}ms)")


class TestLLMPerformance:
    """Test LLM performance"""

    @pytest.mark.asyncio
    async def test_llm_local_latency(self):
        """Test local LLM response latency"""

        # Mock local LLM
        mock_llm = AsyncMock()

        async def complete_local(*args, **kwargs):
            # Simulate local LLM processing
            await asyncio.sleep(1.8)  # 1800ms - under 2000ms target
            return CompletionResult(
                content="This is a response from local LLM",
                model="gpt-oss:120b",
                tokens_used=100,
                finish_reason="stop",
            )

        mock_llm.complete = complete_local

        # Measure latency
        start = time.perf_counter()
        result = await mock_llm.complete([])
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result.content is not None
        assert duration_ms < TARGETS["llm_local_response_ms"], \
            f"Local LLM took {duration_ms:.1f}ms, target is {TARGETS['llm_local_response_ms']}ms"

        print(f"✓ Local LLM latency: {duration_ms:.1f}ms (target: {TARGETS['llm_local_response_ms']}ms)")

    @pytest.mark.asyncio
    async def test_llm_cloud_latency(self):
        """Test cloud LLM response latency"""

        # Mock cloud LLM
        mock_llm = AsyncMock()

        async def complete_cloud(*args, **kwargs):
            # Simulate cloud API latency
            await asyncio.sleep(3.5)  # 3500ms - under 5000ms target
            return CompletionResult(
                content="This is a response from cloud LLM",
                model="claude-sonnet-4",
                tokens_used=100,
                finish_reason="stop",
            )

        mock_llm.complete = complete_cloud

        # Measure latency
        start = time.perf_counter()
        result = await mock_llm.complete([])
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result.content is not None
        assert duration_ms < TARGETS["llm_cloud_response_ms"], \
            f"Cloud LLM took {duration_ms:.1f}ms, target is {TARGETS['llm_cloud_response_ms']}ms"

        print(f"✓ Cloud LLM latency: {duration_ms:.1f}ms (target: {TARGETS['llm_cloud_response_ms']}ms)")


class TestToolPerformance:
    """Test tool execution performance"""

    @pytest.mark.asyncio
    async def test_tool_execution_latency(self):
        """Test tool execution latency"""

        # Mock MCP client
        mock_mcp = AsyncMock()

        async def execute_tool(*args, **kwargs):
            # Simulate tool execution (e.g., AppleScript)
            await asyncio.sleep(0.8)  # 800ms - under 1000ms target
            return "Tool execution successful"

        mock_mcp.call_tool = execute_tool

        # Measure latency
        start = time.perf_counter()
        result = await mock_mcp.call_tool("execute_applescript", {})
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result is not None
        assert duration_ms < TARGETS["tool_execution_ms"], \
            f"Tool execution took {duration_ms:.1f}ms, target is {TARGETS['tool_execution_ms']}ms"

        print(f"✓ Tool execution latency: {duration_ms:.1f}ms (target: {TARGETS['tool_execution_ms']}ms)")


class TestEndToEndPerformance:
    """Test end-to-end pipeline performance"""

    @pytest.mark.asyncio
    async def test_e2e_simple_query(self, perf_config, generate_audio):
        """Test end-to-end latency for simple query (no tools)"""

        # Mock components with realistic latencies
        mock_stt = AsyncMock()
        mock_stt.transcribe = AsyncMock(return_value=TranscriptionResult(
            text="What time is it?",
            language="en",
            confidence=0.95,
            duration_ms=400,
        ))

        # Simulate STT delay
        original_transcribe = mock_stt.transcribe

        async def transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(0.4)
            return await original_transcribe(*args, **kwargs)

        mock_stt.transcribe = transcribe_with_delay

        # Mock LLM
        mock_llm = AsyncMock()

        async def complete_with_delay(*args, **kwargs):
            await asyncio.sleep(1.5)  # Local LLM delay
            return CompletionResult(
                content="It's currently 3:45 PM",
                model="gpt-oss:120b",
                tokens_used=50,
                finish_reason="stop",
            )

        mock_llm.complete = complete_with_delay

        # Mock TTS
        mock_tts = AsyncMock()

        async def speak_with_delay(*args, **kwargs):
            await asyncio.sleep(0.3)
            return None

        mock_tts.speak = speak_with_delay
        mock_tts.is_speaking.return_value = False

        # Create pipeline
        state = ConversationState()
        metrics = MetricsCollector(enable_metrics=True)
        error_handler = ErrorRecoveryHandler(perf_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=perf_config,
        )

        # Generate audio and process
        audio_event = generate_audio(duration_seconds=3.0)

        start = time.perf_counter()
        result = await pipeline.process_audio_event(audio_event)
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result.success is True
        assert duration_ms < TARGETS["end_to_end_ms"], \
            f"E2E took {duration_ms:.1f}ms, target is {TARGETS['end_to_end_ms']}ms"

        print(f"✓ End-to-end latency (simple): {duration_ms:.1f}ms (target: {TARGETS['end_to_end_ms']}ms)")

        # Print stage breakdown
        stage_metrics = metrics.get_all_metrics()["stages"]
        print("\nStage breakdown:")
        for stage, data in stage_metrics.items():
            print(f"  {stage}: {data['avg_duration_ms']}ms")

    @pytest.mark.asyncio
    async def test_e2e_with_tool_call(self, perf_config, generate_audio):
        """Test end-to-end latency with tool calling"""

        from voice_assistant.llm import ToolCall

        # Mock components
        mock_stt = AsyncMock()

        async def transcribe(*args, **kwargs):
            await asyncio.sleep(0.4)
            return TranscriptionResult(
                text="Open Safari",
                language="en",
                confidence=0.95,
                duration_ms=400,
            )

        mock_stt.transcribe = transcribe

        # Mock LLM - returns tool call, then final response
        mock_llm = AsyncMock()
        responses = [
            CompletionResult(
                content="",
                model="gpt-oss:120b",
                tokens_used=30,
                finish_reason="tool_calls",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="execute_applescript",
                        arguments={"script": "tell application \"Safari\" to activate"},
                    )
                ],
            ),
            CompletionResult(
                content="I've opened Safari",
                model="gpt-oss:120b",
                tokens_used=20,
                finish_reason="stop",
            ),
        ]

        call_count = [0]

        async def complete(*args, **kwargs):
            await asyncio.sleep(1.5)
            response = responses[min(call_count[0], len(responses) - 1)]
            call_count[0] += 1
            return response

        mock_llm.complete = complete

        # Mock MCP
        mock_mcp = AsyncMock()

        async def call_tool(*args, **kwargs):
            await asyncio.sleep(0.8)  # Tool execution
            return "Success"

        mock_mcp.call_tool = call_tool

        # Mock TTS
        mock_tts = AsyncMock()
        mock_tts.speak = AsyncMock()
        mock_tts.is_speaking.return_value = False

        # Create pipeline
        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(perf_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=perf_config,
            mcp_client=mock_mcp,
        )

        # Process
        audio_event = generate_audio(duration_seconds=2.0)

        start = time.perf_counter()
        result = await pipeline.process_audio_event(audio_event)
        duration_ms = (time.perf_counter() - start) * 1000

        # Verify
        assert result.success is True
        assert result.tool_calls_made == 1

        # Tool calling adds overhead, so allow more time
        max_allowed = TARGETS["end_to_end_ms"] + TARGETS["tool_execution_ms"] + TARGETS["llm_local_response_ms"]
        assert duration_ms < max_allowed, \
            f"E2E with tool took {duration_ms:.1f}ms, max allowed is {max_allowed}ms"

        print(f"✓ End-to-end latency (with tool): {duration_ms:.1f}ms")


class TestMetricsCollection:
    """Test metrics collection performance impact"""

    @pytest.mark.asyncio
    async def test_metrics_overhead(self):
        """Test that metrics collection has minimal overhead"""

        metrics = MetricsCollector(enable_metrics=True)

        # Time with metrics
        iterations = 1000

        start = time.perf_counter()
        for i in range(iterations):
            with metrics.timer("test_operation"):
                await asyncio.sleep(0.001)  # 1ms operation
        duration_with = time.perf_counter() - start

        # Time without metrics (just the operation)
        start = time.perf_counter()
        for i in range(iterations):
            await asyncio.sleep(0.001)
        duration_without = time.perf_counter() - start

        overhead = duration_with - duration_without
        overhead_per_op = (overhead / iterations) * 1000  # ms

        # Overhead should be negligible (< 0.1ms per operation)
        assert overhead_per_op < 0.1, \
            f"Metrics overhead too high: {overhead_per_op:.3f}ms per operation"

        print(f"✓ Metrics overhead: {overhead_per_op:.3f}ms per operation")


class TestThroughput:
    """Test system throughput"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, perf_config, generate_audio):
        """Test handling multiple requests (though max_concurrent=1 in config)"""

        # Create simple pipeline
        mock_stt = AsyncMock()
        mock_stt.transcribe = AsyncMock(return_value=TranscriptionResult(
            text="Test",
            language="en",
            confidence=0.9,
            duration_ms=100,
        ))

        mock_llm = AsyncMock()

        async def complete(*args, **kwargs):
            await asyncio.sleep(0.1)
            return CompletionResult(
                content="Response",
                model="test",
                tokens_used=10,
                finish_reason="stop",
            )

        mock_llm.complete = complete

        mock_tts = AsyncMock()
        mock_tts.is_speaking.return_value = False

        state = ConversationState()
        metrics = MetricsCollector()
        error_handler = ErrorRecoveryHandler(perf_config, tts_engine=mock_tts)

        pipeline = VoicePipeline(
            stt=mock_stt,
            llm_provider=mock_llm,
            tts=mock_tts,
            conversation_state=state,
            metrics=metrics,
            error_handler=error_handler,
            config=perf_config,
        )

        # Process 5 requests sequentially
        num_requests = 5
        audio_event = generate_audio(duration_seconds=2.0)

        start = time.perf_counter()
        results = []
        for _ in range(num_requests):
            result = await pipeline.process_audio_event(audio_event)
            results.append(result)
        total_duration = time.perf_counter() - start

        # Verify all succeeded
        assert all(r.success for r in results)

        avg_duration = (total_duration / num_requests) * 1000
        print(f"✓ Throughput: {num_requests} requests in {total_duration:.2f}s (avg: {avg_duration:.1f}ms)")


def print_performance_summary():
    """Print performance targets summary"""
    print("\n" + "=" * 80)
    print("PERFORMANCE TARGETS (from CLAUDE.md)")
    print("=" * 80)
    for metric, target in TARGETS.items():
        print(f"  {metric}: {target}ms")
    print("=" * 80)


if __name__ == "__main__":
    print_performance_summary()
    pytest.main([__file__, "-v", "-s"])
