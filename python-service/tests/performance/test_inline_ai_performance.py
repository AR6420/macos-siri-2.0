"""
Performance benchmarking tests for enhanced in-line AI feature.

Measures latency, throughput, memory usage, and CPU usage for all operations.
"""

import pytest
import asyncio
import time
import psutil
import statistics
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from voice_assistant.inline_ai.enhanced_handler import EnhancedInlineAIHandler
from voice_assistant.llm.base import CompletionResult


# Performance targets (in milliseconds)
TARGETS = {
    "button_appearance": 100,
    "menu_open": 150,
    "proofread_100_words": 2000,
    "rewrite_100_words": 2000,
    "summarize_500_words": 3000,
    "key_points_500_words": 3000,
    "make_list": 500,
    "make_table": 3000,
    "compose": 3000,
}


class PerformanceMetrics:
    """Track performance metrics"""

    def __init__(self):
        self.latencies: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []

    def add_measurement(self, latency_ms: float, memory_mb: float, cpu_percent: float):
        self.latencies.append(latency_ms)
        self.memory_usage.append(memory_mb)
        self.cpu_usage.append(cpu_percent)

    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistics"""
        return {
            "latency": {
                "mean": statistics.mean(self.latencies),
                "median": statistics.median(self.latencies),
                "p95": self._percentile(self.latencies, 95),
                "p99": self._percentile(self.latencies, 99),
                "min": min(self.latencies),
                "max": max(self.latencies),
            },
            "memory_mb": {
                "mean": statistics.mean(self.memory_usage),
                "max": max(self.memory_usage),
            },
            "cpu_percent": {
                "mean": statistics.mean(self.cpu_usage),
                "max": max(self.cpu_usage),
            },
        }

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


@pytest.fixture
def mock_llm_fast():
    """Mock LLM with fast responses"""
    llm = AsyncMock()

    async def fast_complete(*args, **kwargs):
        await asyncio.sleep(0.01)  # Simulate minimal latency
        return CompletionResult(
            content="Fast response",
            model="test",
            tokens_used=10,
            finish_reason="stop"
        )

    llm.complete = fast_complete
    return llm


@pytest.fixture
def mock_llm_realistic():
    """Mock LLM with realistic latencies"""
    llm = AsyncMock()

    async def realistic_complete(*args, **kwargs):
        # Simulate realistic API latency (500ms-1500ms)
        await asyncio.sleep(0.5 + (0.5 * asyncio.get_event_loop().time() % 1))
        return CompletionResult(
            content="Realistic response",
            model="test",
            tokens_used=100,
            finish_reason="stop"
        )

    llm.complete = realistic_complete
    return llm


@pytest.fixture
def process():
    """Get current process for monitoring"""
    return psutil.Process()


def measure_operation(func):
    """Decorator to measure operation performance"""

    async def wrapper(*args, **kwargs):
        process = psutil.Process()

        # Measure before
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()

        # Execute
        result = await func(*args, **kwargs)

        # Measure after
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024
        end_cpu = process.cpu_percent()

        latency_ms = (end_time - start_time) * 1000
        memory_delta = end_memory - start_memory
        cpu_usage = max(start_cpu, end_cpu)

        return result, {
            "latency_ms": latency_ms,
            "memory_mb": memory_delta,
            "cpu_percent": cpu_usage,
        }

    return wrapper


# ============================================================================
# PROOFREAD PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_proofread_latency_100_words(mock_llm_realistic):
    """Benchmark proofread operation with 100 words"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    text = " ".join(["word"] * 100)

    metrics = PerformanceMetrics()

    # Run 10 iterations
    for _ in range(10):
        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "proofread",
                "text": text
            })

        result, perf = await run()
        metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

    stats = metrics.get_stats()
    print(f"\nProofread 100 words:")
    print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
    print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")
    print(f"  Memory: {stats['memory_mb']['mean']:.2f}MB")

    assert stats["latency"]["p95"] < TARGETS["proofread_100_words"]


@pytest.mark.asyncio
async def test_proofread_various_lengths(mock_llm_realistic):
    """Benchmark proofread with various text lengths"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)

    results = {}
    for word_count in [10, 50, 100, 200, 500]:
        text = " ".join(["word"] * word_count)

        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "proofread",
                "text": text
            })

        _, perf = await run()
        results[word_count] = perf["latency_ms"]

    print("\nProofread latency by word count:")
    for word_count, latency in results.items():
        print(f"  {word_count} words: {latency:.0f}ms")

    # Verify scaling is reasonable (not exponential)
    assert results[500] < results[100] * 3


# ============================================================================
# REWRITE PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_rewrite_latency(mock_llm_realistic):
    """Benchmark rewrite operation"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    text = " ".join(["This is a test sentence."] * 20)  # ~100 words

    metrics = PerformanceMetrics()

    for _ in range(10):
        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "rewrite",
                "text": text,
                "params": {"tone": "friendly"}
            })

        result, perf = await run()
        metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

    stats = metrics.get_stats()
    print(f"\nRewrite 100 words:")
    print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
    print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")

    assert stats["latency"]["p95"] < TARGETS["rewrite_100_words"]


# ============================================================================
# SUMMARIZE PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_summarize_latency(mock_llm_realistic):
    """Benchmark summarize operation"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    text = " ".join(["This is a sentence in the article."] * 100)  # ~700 words

    metrics = PerformanceMetrics()

    for _ in range(5):
        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "summarize",
                "text": text
            })

        result, perf = await run()
        metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

    stats = metrics.get_stats()
    print(f"\nSummarize 700 words:")
    print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
    print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")

    assert stats["latency"]["p95"] < TARGETS["summarize_500_words"] * 1.5


# ============================================================================
# KEY POINTS PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_key_points_latency(mock_llm_realistic):
    """Benchmark key points extraction"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    text = " ".join(["Important point about the topic."] * 100)

    @measure_operation
    async def run():
        return await handler.handle_command({
            "action": "key_points",
            "text": text
        })

    result, perf = await run()

    print(f"\nKey points extraction:")
    print(f"  Latency: {perf['latency_ms']:.0f}ms")

    assert perf["latency_ms"] < TARGETS["key_points_500_words"]


# ============================================================================
# FORMATTING PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_make_list_latency(mock_llm_fast):
    """Benchmark make_list operation (no LLM needed)"""

    handler = EnhancedInlineAIHandler(mock_llm_fast)
    text = "Item one. Item two. Item three. Item four. Item five."

    metrics = PerformanceMetrics()

    for _ in range(20):
        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "make_list",
                "text": text
            })

        result, perf = await run()
        metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

    stats = metrics.get_stats()
    print(f"\nMake list:")
    print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
    print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")

    assert stats["latency"]["p95"] < TARGETS["make_list"]


@pytest.mark.asyncio
async def test_make_table_latency(mock_llm_realistic):
    """Benchmark make_table operation"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    text = "Product A costs $10, Product B costs $20, Product C costs $30"

    @measure_operation
    async def run():
        return await handler.handle_command({
            "action": "make_table",
            "text": text
        })

    result, perf = await run()

    print(f"\nMake table:")
    print(f"  Latency: {perf['latency_ms']:.0f}ms")

    assert perf["latency_ms"] < TARGETS["make_table"]


# ============================================================================
# COMPOSE PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_compose_latency(mock_llm_realistic):
    """Benchmark compose operation"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    prompt = "Write a professional email thanking someone for their help"

    metrics = PerformanceMetrics()

    for _ in range(5):
        @measure_operation
        async def run():
            return await handler.handle_command({
                "action": "compose",
                "text": prompt
            })

        result, perf = await run()
        metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

    stats = metrics.get_stats()
    print(f"\nCompose email:")
    print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
    print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")

    assert stats["latency"]["p95"] < TARGETS["compose"]


# ============================================================================
# CONCURRENT OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_operations_throughput(mock_llm_realistic):
    """Test throughput with concurrent operations"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)

    async def single_operation(text_id: int):
        return await handler.handle_command({
            "action": "proofread",
            "text": f"Test text {text_id} " * 50
        })

    # Run 10 concurrent operations
    start = time.time()
    results = await asyncio.gather(*[single_operation(i) for i in range(10)])
    elapsed = time.time() - start

    throughput = 10 / elapsed  # operations per second
    print(f"\nConcurrent operations:")
    print(f"  10 operations completed in {elapsed:.2f}s")
    print(f"  Throughput: {throughput:.2f} ops/sec")

    assert all(r["status"] == "success" for r in results)


# ============================================================================
# MEMORY USAGE
# ============================================================================

@pytest.mark.asyncio
async def test_memory_usage_sustained(mock_llm_realistic):
    """Test memory usage over sustained operations"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)
    process = psutil.Process()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Run 100 operations
    for i in range(100):
        await handler.handle_command({
            "action": "proofread",
            "text": f"Test text iteration {i} " * 20
        })

    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    print(f"\nMemory usage after 100 operations:")
    print(f"  Initial: {initial_memory:.2f}MB")
    print(f"  Final: {final_memory:.2f}MB")
    print(f"  Increase: {memory_increase:.2f}MB")

    # Memory increase should be minimal (no leaks)
    assert memory_increase < 50  # Allow up to 50MB increase


# ============================================================================
# CPU USAGE
# ============================================================================

@pytest.mark.asyncio
async def test_cpu_usage_idle():
    """Test CPU usage when idle"""

    handler = EnhancedInlineAIHandler(AsyncMock())
    process = psutil.Process()

    # Let process settle
    await asyncio.sleep(1)

    cpu_measurements = []
    for _ in range(10):
        cpu_measurements.append(process.cpu_percent(interval=0.1))

    avg_cpu = statistics.mean(cpu_measurements)
    print(f"\nIdle CPU usage: {avg_cpu:.2f}%")

    # Should be very low when idle
    assert avg_cpu < 5.0


# ============================================================================
# LOCAL VS CLOUD COMPARISON
# ============================================================================

@pytest.mark.asyncio
async def test_local_vs_cloud_latency():
    """Compare local vs cloud LLM performance"""

    # Mock local LLM (faster)
    local_llm = AsyncMock()

    async def local_complete(*args, **kwargs):
        await asyncio.sleep(0.2)  # 200ms
        return CompletionResult(
            content="Local response",
            model="local",
            tokens_used=100,
            finish_reason="stop"
        )

    local_llm.complete = local_complete

    # Mock cloud LLM (slower)
    cloud_llm = AsyncMock()

    async def cloud_complete(*args, **kwargs):
        await asyncio.sleep(1.0)  # 1000ms
        return CompletionResult(
            content="Cloud response",
            model="cloud",
            tokens_used=100,
            finish_reason="stop"
        )

    cloud_llm.complete = cloud_complete

    text = "Test text " * 50

    # Test local
    local_handler = EnhancedInlineAIHandler(local_llm)
    start = time.time()
    await local_handler.handle_command({"action": "proofread", "text": text})
    local_latency = (time.time() - start) * 1000

    # Test cloud
    cloud_handler = EnhancedInlineAIHandler(cloud_llm)
    start = time.time()
    await cloud_handler.handle_command({"action": "proofread", "text": text})
    cloud_latency = (time.time() - start) * 1000

    print(f"\nLocal vs Cloud latency:")
    print(f"  Local: {local_latency:.0f}ms")
    print(f"  Cloud: {cloud_latency:.0f}ms")
    print(f"  Speedup: {cloud_latency / local_latency:.1f}x")

    assert local_latency < cloud_latency


# ============================================================================
# STRESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_stress_rapid_fire(mock_llm_fast):
    """Stress test with rapid-fire requests"""

    handler = EnhancedInlineAIHandler(mock_llm_fast)

    start = time.time()
    tasks = []

    # Fire 50 requests as fast as possible
    for i in range(50):
        task = handler.handle_command({
            "action": "proofread",
            "text": f"Request {i}"
        })
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    print(f"\nStress test (50 rapid requests):")
    print(f"  Completed in {elapsed:.2f}s")
    print(f"  Throughput: {50 / elapsed:.2f} ops/sec")

    assert all(r["status"] == "success" for r in results)


@pytest.mark.asyncio
async def test_stress_large_text(mock_llm_realistic):
    """Stress test with very large text"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)

    # 10,000 words
    text = " ".join(["word"] * 10000)

    @measure_operation
    async def run():
        return await handler.handle_command({
            "action": "summarize",
            "text": text
        })

    result, perf = await run()

    print(f"\nLarge text (10,000 words):")
    print(f"  Latency: {perf['latency_ms']:.0f}ms")
    print(f"  Memory: {perf['memory_mb']:.2f}MB")

    assert result["status"] == "success"
    # Should complete within reasonable time
    assert perf["latency_ms"] < 10000  # 10 seconds max


# ============================================================================
# BENCHMARK REPORT
# ============================================================================

@pytest.mark.asyncio
async def test_generate_full_benchmark_report(mock_llm_realistic):
    """Generate comprehensive benchmark report"""

    handler = EnhancedInlineAIHandler(mock_llm_realistic)

    operations = [
        ("proofread", {"action": "proofread", "text": " ".join(["word"] * 100)}),
        ("rewrite", {"action": "rewrite", "text": " ".join(["word"] * 100), "params": {"tone": "friendly"}}),
        ("summarize", {"action": "summarize", "text": " ".join(["word"] * 500)}),
        ("key_points", {"action": "key_points", "text": " ".join(["word"] * 500)}),
        ("make_list", {"action": "make_list", "text": "Item 1. Item 2. Item 3."}),
        ("compose", {"action": "compose", "text": "Write a short email"}),
    ]

    report = {}

    for op_name, command in operations:
        metrics = PerformanceMetrics()

        for _ in range(5):
            @measure_operation
            async def run():
                return await handler.handle_command(command)

            result, perf = await run()
            metrics.add_measurement(perf["latency_ms"], perf["memory_mb"], perf["cpu_percent"])

        report[op_name] = metrics.get_stats()

    print("\n" + "=" * 70)
    print("COMPREHENSIVE PERFORMANCE BENCHMARK REPORT")
    print("=" * 70)

    for op_name, stats in report.items():
        target = TARGETS.get(f"{op_name}_100_words", TARGETS.get(op_name, "N/A"))
        print(f"\n{op_name.upper()}:")
        print(f"  Mean latency: {stats['latency']['mean']:.0f}ms")
        print(f"  P95 latency: {stats['latency']['p95']:.0f}ms")
        print(f"  Target: {target if isinstance(target, str) else f'{target}ms'}")
        print(f"  Memory: {stats['memory_mb']['mean']:.2f}MB")
        print(f"  CPU: {stats['cpu_percent']['mean']:.1f}%")

        if not isinstance(target, str):
            status = "✓ PASS" if stats['latency']['p95'] < target else "✗ FAIL"
            print(f"  Status: {status}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
