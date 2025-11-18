"""
Metrics collection for Enhanced Inline AI feature.

Privacy-respecting usage tracking to understand feature adoption and performance.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import asyncio
from pathlib import Path


@dataclass
class ActionMetric:
    """Metrics for a single action execution"""

    action: str  # e.g., "proofread", "rewrite_friendly", "make_list"
    timestamp: float
    input_length: int  # Characters in input text
    output_length: int  # Characters in output text
    latency_ms: int  # Processing time in milliseconds
    success: bool  # Whether action completed successfully
    error_type: Optional[str] = None  # If failed, what error occurred
    tokens_used: int = 0  # LLM tokens consumed
    cache_hit: bool = False  # Whether result was cached


@dataclass
class SessionMetrics:
    """Metrics for a user session"""

    session_id: str
    start_time: float
    end_time: Optional[float] = None
    actions: List[ActionMetric] = field(default_factory=list)
    total_text_processed: int = 0  # Total characters processed
    total_latency_ms: int = 0  # Total processing time
    total_tokens_used: int = 0  # Total LLM tokens

    def add_action(self, metric: ActionMetric):
        """Add action metric to session"""
        self.actions.append(metric)
        self.total_text_processed += metric.input_length
        self.total_latency_ms += metric.latency_ms
        self.total_tokens_used += metric.tokens_used

    def end_session(self):
        """Mark session as ended"""
        self.end_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary statistics"""
        if not self.actions:
            return {}

        action_counts = {}
        for action in self.actions:
            action_counts[action.action] = action_counts.get(action.action, 0) + 1

        successful_actions = [a for a in self.actions if a.success]
        failed_actions = [a for a in self.actions if not a.success]

        return {
            "session_id": self.session_id,
            "duration_seconds": (self.end_time or time.time()) - self.start_time,
            "total_actions": len(self.actions),
            "successful_actions": len(successful_actions),
            "failed_actions": len(failed_actions),
            "action_breakdown": action_counts,
            "total_text_processed": self.total_text_processed,
            "total_latency_ms": self.total_latency_ms,
            "total_tokens_used": self.total_tokens_used,
            "average_latency_ms": self.total_latency_ms / len(self.actions) if self.actions else 0,
        }


@dataclass
class AggregatedMetrics:
    """Aggregated metrics across all sessions"""

    total_sessions: int = 0
    total_actions: int = 0
    action_frequency: Dict[str, int] = field(default_factory=dict)
    average_latency_by_action: Dict[str, float] = field(default_factory=dict)
    success_rate_by_action: Dict[str, float] = field(default_factory=dict)
    total_tokens_used: int = 0
    total_text_processed: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class MetricsCollector:
    """
    Privacy-respecting metrics collector for inline AI.

    PRIVACY NOTES:
    - No actual text content is logged
    - Only metadata (lengths, timings, success/failure)
    - Can be completely disabled via config
    - Metrics stored locally only
    - No telemetry sent to external servers
    """

    def __init__(self, enabled: bool = True, metrics_dir: Optional[Path] = None):
        self.enabled = enabled
        self.metrics_dir = metrics_dir or Path.home() / ".voice-assistant" / "metrics"
        self.current_session: Optional[SessionMetrics] = None
        self.aggregated = AggregatedMetrics()

        if self.enabled:
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
            self._load_aggregated_metrics()

    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new metrics session"""
        if not self.enabled:
            return ""

        session_id = session_id or f"session_{int(time.time())}"
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=time.time()
        )
        return session_id

    def end_session(self):
        """End current session and save metrics"""
        if not self.enabled or not self.current_session:
            return

        self.current_session.end_session()
        self._save_session_metrics(self.current_session)
        self._update_aggregated_metrics(self.current_session)
        self.current_session = None

    def record_action(
        self,
        action: str,
        input_length: int,
        output_length: int,
        latency_ms: int,
        success: bool,
        error_type: Optional[str] = None,
        tokens_used: int = 0,
        cache_hit: bool = False
    ):
        """Record an action execution"""
        if not self.enabled:
            return

        # Ensure session exists
        if not self.current_session:
            self.start_session()

        metric = ActionMetric(
            action=action,
            timestamp=time.time(),
            input_length=input_length,
            output_length=output_length,
            latency_ms=latency_ms,
            success=success,
            error_type=error_type,
            tokens_used=tokens_used,
            cache_hit=cache_hit
        )

        self.current_session.add_action(metric)

    def get_action_stats(self, action: str) -> Dict[str, Any]:
        """Get statistics for a specific action"""
        if action not in self.aggregated.action_frequency:
            return {}

        return {
            "total_uses": self.aggregated.action_frequency.get(action, 0),
            "average_latency_ms": self.aggregated.average_latency_by_action.get(action, 0),
            "success_rate": self.aggregated.success_rate_by_action.get(action, 0),
        }

    def get_most_used_actions(self, limit: int = 5) -> List[tuple]:
        """Get most frequently used actions"""
        sorted_actions = sorted(
            self.aggregated.action_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_actions[:limit]

    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        return {
            "total_sessions": self.aggregated.total_sessions,
            "total_actions": self.aggregated.total_actions,
            "total_tokens_used": self.aggregated.total_tokens_used,
            "total_text_processed_chars": self.aggregated.total_text_processed,
            "most_used_actions": self.get_most_used_actions(),
            "action_breakdown": self.aggregated.action_frequency,
            "average_latencies": self.aggregated.average_latency_by_action,
            "success_rates": self.aggregated.success_rate_by_action,
            "error_types": self.aggregated.error_types,
        }

    def _save_session_metrics(self, session: SessionMetrics):
        """Save session metrics to file"""
        if not self.enabled:
            return

        date_str = datetime.fromtimestamp(session.start_time).strftime("%Y-%m-%d")
        session_file = self.metrics_dir / f"session_{date_str}_{session.session_id}.json"

        data = {
            "session": asdict(session),
            "summary": session.get_summary()
        }

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)

    def _update_aggregated_metrics(self, session: SessionMetrics):
        """Update aggregated metrics with session data"""
        if not self.enabled:
            return

        self.aggregated.total_sessions += 1
        self.aggregated.total_actions += len(session.actions)
        self.aggregated.total_tokens_used += session.total_tokens_used
        self.aggregated.total_text_processed += session.total_text_processed

        # Update action-specific metrics
        action_latencies: Dict[str, List[int]] = {}
        action_successes: Dict[str, List[bool]] = {}

        for action in session.actions:
            # Frequency
            self.aggregated.action_frequency[action.action] = \
                self.aggregated.action_frequency.get(action.action, 0) + 1

            # Latencies
            if action.action not in action_latencies:
                action_latencies[action.action] = []
            action_latencies[action.action].append(action.latency_ms)

            # Successes
            if action.action not in action_successes:
                action_successes[action.action] = []
            action_successes[action.action].append(action.success)

            # Errors
            if not action.success and action.error_type:
                self.aggregated.error_types[action.error_type] = \
                    self.aggregated.error_types.get(action.error_type, 0) + 1

        # Calculate averages
        for action_name, latencies in action_latencies.items():
            self.aggregated.average_latency_by_action[action_name] = sum(latencies) / len(latencies)

        for action_name, successes in action_successes.items():
            success_count = sum(1 for s in successes if s)
            self.aggregated.success_rate_by_action[action_name] = success_count / len(successes)

        # Save aggregated metrics
        self._save_aggregated_metrics()

    def _save_aggregated_metrics(self):
        """Save aggregated metrics to file"""
        if not self.enabled:
            return

        aggregated_file = self.metrics_dir / "aggregated_metrics.json"

        with open(aggregated_file, "w") as f:
            json.dump(self.aggregated.to_dict(), f, indent=2)

    def _load_aggregated_metrics(self):
        """Load aggregated metrics from file"""
        if not self.enabled:
            return

        aggregated_file = self.metrics_dir / "aggregated_metrics.json"

        if not aggregated_file.exists():
            return

        try:
            with open(aggregated_file, "r") as f:
                data = json.load(f)
                self.aggregated = AggregatedMetrics(**data)
        except Exception as e:
            print(f"Failed to load aggregated metrics: {e}")

    def generate_report(self) -> str:
        """Generate human-readable metrics report"""
        stats = self.get_overall_stats()

        report = ["=" * 70]
        report.append("INLINE AI METRICS REPORT")
        report.append("=" * 70)
        report.append("")

        report.append("OVERALL STATISTICS:")
        report.append(f"  Total Sessions: {stats['total_sessions']}")
        report.append(f"  Total Actions: {stats['total_actions']}")
        report.append(f"  Total Text Processed: {stats['total_text_processed_chars']:,} characters")
        report.append(f"  Total Tokens Used: {stats['total_tokens_used']:,}")
        report.append("")

        report.append("MOST USED ACTIONS:")
        for action, count in stats['most_used_actions']:
            percentage = (count / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
            report.append(f"  {action}: {count} times ({percentage:.1f}%)")
        report.append("")

        report.append("AVERAGE LATENCIES:")
        for action, latency in stats['average_latencies'].items():
            report.append(f"  {action}: {latency:.0f}ms")
        report.append("")

        report.append("SUCCESS RATES:")
        for action, rate in stats['success_rates'].items():
            report.append(f"  {action}: {rate * 100:.1f}%")
        report.append("")

        if stats['error_types']:
            report.append("ERROR TYPES:")
            for error_type, count in stats['error_types'].items():
                report.append(f"  {error_type}: {count} occurrences")
            report.append("")

        report.append("=" * 70)

        return "\n".join(report)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(enabled: bool = True) -> MetricsCollector:
    """Get or create global metrics collector"""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(enabled=enabled)

    return _metrics_collector


def disable_metrics():
    """Disable metrics collection globally"""
    global _metrics_collector
    _metrics_collector = MetricsCollector(enabled=False)


# Context manager for automatic session tracking
class MetricsSession:
    """Context manager for automatic metrics session tracking"""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or get_metrics_collector()

    def __enter__(self):
        self.collector.start_session()
        return self.collector

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.collector.end_session()


# Example usage
if __name__ == "__main__":
    # Create collector
    collector = MetricsCollector(enabled=True)

    # Start session
    collector.start_session()

    # Record some actions
    collector.record_action(
        action="proofread",
        input_length=100,
        output_length=95,
        latency_ms=1200,
        success=True,
        tokens_used=50
    )

    collector.record_action(
        action="rewrite_friendly",
        input_length=50,
        output_length=60,
        latency_ms=1500,
        success=True,
        tokens_used=45
    )

    collector.record_action(
        action="summarize",
        input_length=500,
        output_length=100,
        latency_ms=2000,
        success=True,
        tokens_used=80
    )

    # End session
    collector.end_session()

    # Print report
    print(collector.generate_report())
