"""
Performance Metrics and Monitoring

Tracks performance metrics for each pipeline stage and overall system health.
"""

import logging
import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage"""
    stage_name: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration"""
        if self.call_count == 0:
            return 0.0
        return self.total_duration_ms / self.call_count

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)"""
        if self.call_count == 0:
            return 0.0
        return self.success_count / self.call_count

    @property
    def p95_duration_ms(self) -> float:
        """Calculate 95th percentile duration"""
        if not self.recent_durations:
            return 0.0
        sorted_durations = sorted(self.recent_durations)
        index = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(index, len(sorted_durations) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/export"""
        return {
            "stage": self.stage_name,
            "calls": self.call_count,
            "success": self.success_count,
            "errors": self.error_count,
            "success_rate": f"{self.success_rate * 100:.1f}%",
            "avg_duration_ms": f"{self.avg_duration_ms:.1f}",
            "min_duration_ms": f"{self.min_duration_ms:.1f}",
            "max_duration_ms": f"{self.max_duration_ms:.1f}",
            "p95_duration_ms": f"{self.p95_duration_ms:.1f}",
        }


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, stage_name: str, metrics_collector: 'MetricsCollector'):
        self.stage_name = stage_name
        self.metrics = metrics_collector
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.success: bool = True

    def __enter__(self) -> 'PerformanceTimer':
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000

        # Determine if operation was successful
        self.success = exc_type is None

        # Record metrics
        self.metrics.record_stage(
            self.stage_name,
            duration_ms,
            self.success
        )

        return False  # Don't suppress exceptions

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.end_time == 0.0:
            return (time.perf_counter() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000


class MetricsCollector:
    """
    Collect and manage performance metrics.

    Features:
    - Per-stage timing and success tracking
    - End-to-end pipeline metrics
    - Periodic metric logging
    - Error rate tracking
    - Performance trend analysis
    """

    def __init__(
        self,
        enable_metrics: bool = True,
        log_interval_seconds: int = 60,
    ):
        """
        Initialize metrics collector.

        Args:
            enable_metrics: Whether to collect metrics
            log_interval_seconds: How often to log summary metrics
        """
        self.enabled = enable_metrics
        self.log_interval = log_interval_seconds

        # Per-stage metrics
        self._stage_metrics: Dict[str, StageMetrics] = defaultdict(
            lambda: StageMetrics(stage_name="unknown")
        )

        # System-level metrics
        self._system_metrics = {
            "start_time": time.time(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
        }

        # End-to-end pipeline metrics
        self._e2e_durations: deque = deque(maxlen=100)

        # Error tracking
        self._recent_errors: deque = deque(maxlen=50)

        # Background logging task
        self._log_task: Optional[asyncio.Task] = None

        if self.enabled:
            logger.info(
                f"Metrics collection enabled, logging every {log_interval_seconds}s"
            )

    def record_stage(
        self,
        stage_name: str,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """
        Record metrics for a pipeline stage.

        Args:
            stage_name: Name of the stage
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
        """
        if not self.enabled:
            return

        metrics = self._stage_metrics[stage_name]
        metrics.stage_name = stage_name
        metrics.call_count += 1
        metrics.total_duration_ms += duration_ms
        metrics.recent_durations.append(duration_ms)

        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1

        metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
        metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)

        # Log slow operations
        if duration_ms > 5000:  # 5 seconds
            logger.warning(
                f"Slow operation: {stage_name} took {duration_ms:.1f}ms"
            )

    def record_request(self, success: bool, e2e_duration_ms: float) -> None:
        """
        Record end-to-end request metrics.

        Args:
            success: Whether the request succeeded
            e2e_duration_ms: End-to-end duration in milliseconds
        """
        if not self.enabled:
            return

        self._system_metrics["total_requests"] += 1

        if success:
            self._system_metrics["successful_requests"] += 1
        else:
            self._system_metrics["failed_requests"] += 1

        self._e2e_durations.append(e2e_duration_ms)

    def record_error(
        self,
        stage_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error.

        Args:
            stage_name: Stage where error occurred
            error: The error
            context: Optional context information
        """
        if not self.enabled:
            return

        error_record = {
            "timestamp": time.time(),
            "stage": stage_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        self._recent_errors.append(error_record)

    def timer(self, stage_name: str) -> PerformanceTimer:
        """
        Create a performance timer context manager.

        Args:
            stage_name: Name of the stage being timed

        Returns:
            PerformanceTimer context manager

        Example:
            with metrics.timer("stt"):
                result = await stt.transcribe(audio)
        """
        return PerformanceTimer(stage_name, self)

    def get_stage_metrics(self, stage_name: str) -> Optional[StageMetrics]:
        """Get metrics for a specific stage"""
        return self._stage_metrics.get(stage_name)

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.

        Returns:
            Dictionary of all metrics
        """
        if not self.enabled:
            return {"enabled": False}

        uptime_seconds = time.time() - self._system_metrics["start_time"]

        # Calculate E2E metrics
        e2e_avg = statistics.mean(self._e2e_durations) if self._e2e_durations else 0.0
        e2e_p95 = 0.0
        if self._e2e_durations:
            sorted_e2e = sorted(self._e2e_durations)
            index = int(len(sorted_e2e) * 0.95)
            e2e_p95 = sorted_e2e[min(index, len(sorted_e2e) - 1)]

        return {
            "system": {
                "uptime_seconds": uptime_seconds,
                "total_requests": self._system_metrics["total_requests"],
                "successful_requests": self._system_metrics["successful_requests"],
                "failed_requests": self._system_metrics["failed_requests"],
                "success_rate": (
                    self._system_metrics["successful_requests"] /
                    self._system_metrics["total_requests"]
                    if self._system_metrics["total_requests"] > 0
                    else 0.0
                ),
            },
            "end_to_end": {
                "avg_duration_ms": e2e_avg,
                "p95_duration_ms": e2e_p95,
                "request_count": len(self._e2e_durations),
            },
            "stages": {
                name: metrics.to_dict()
                for name, metrics in self._stage_metrics.items()
            },
            "recent_errors": list(self._recent_errors)[-10:],  # Last 10 errors
        }

    def log_summary(self) -> None:
        """Log a summary of collected metrics"""
        if not self.enabled:
            return

        metrics = self.get_all_metrics()

        logger.info("=" * 80)
        logger.info("Performance Metrics Summary")
        logger.info("=" * 80)

        # System metrics
        sys_metrics = metrics["system"]
        logger.info(
            f"System: {sys_metrics['total_requests']} requests, "
            f"{sys_metrics['success_rate'] * 100:.1f}% success, "
            f"uptime: {sys_metrics['uptime_seconds']:.0f}s"
        )

        # E2E metrics
        e2e_metrics = metrics["end_to_end"]
        logger.info(
            f"End-to-End: avg={e2e_metrics['avg_duration_ms']:.1f}ms, "
            f"p95={e2e_metrics['p95_duration_ms']:.1f}ms"
        )

        # Stage metrics
        for stage_name, stage_metrics in metrics["stages"].items():
            logger.info(
                f"  {stage_name}: "
                f"avg={stage_metrics['avg_duration_ms']}ms, "
                f"p95={stage_metrics['p95_duration_ms']}ms, "
                f"success={stage_metrics['success_rate']}"
            )

        # Recent errors
        if metrics["recent_errors"]:
            logger.info(f"Recent errors: {len(metrics['recent_errors'])}")
            for error in metrics["recent_errors"][-5:]:  # Last 5
                logger.info(
                    f"  [{error['stage']}] {error['error_type']}: "
                    f"{error['error_message']}"
                )

        logger.info("=" * 80)

    async def start_periodic_logging(self) -> None:
        """Start background task for periodic metric logging"""
        if not self.enabled or self._log_task is not None:
            return

        async def log_loop():
            while True:
                try:
                    await asyncio.sleep(self.log_interval)
                    self.log_summary()
                except asyncio.CancelledError:
                    logger.info("Metrics logging task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in metrics logging: {e}")

        self._log_task = asyncio.create_task(log_loop())
        logger.info("Started periodic metrics logging")

    async def stop_periodic_logging(self) -> None:
        """Stop background metric logging"""
        if self._log_task:
            self._log_task.cancel()
            try:
                await self._log_task
            except asyncio.CancelledError:
                pass
            self._log_task = None
            logger.info("Stopped periodic metrics logging")

    def reset(self) -> None:
        """Reset all metrics"""
        self._stage_metrics.clear()
        self._system_metrics = {
            "start_time": time.time(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
        }
        self._e2e_durations.clear()
        self._recent_errors.clear()
        logger.info("Metrics reset")

    def __repr__(self) -> str:
        return (
            f"MetricsCollector(enabled={self.enabled}, "
            f"requests={self._system_metrics['total_requests']})"
        )
