#!/usr/bin/env python3
"""
Example usage of the Voice Assistant orchestrator.

This demonstrates how to use the orchestration layer independently
of the Swift app for testing and development.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
import numpy as np
from voice_assistant import (
    VoiceAssistant,
    AssistantStatus,
)
from voice_assistant.audio import AudioEvent


async def status_callback(status: AssistantStatus):
    """Handle status updates"""
    print(f"📊 Status: {status.value}")


async def main():
    """Main example function"""
    print("=" * 80)
    print("Voice Assistant Orchestrator Example")
    print("=" * 80)

    # Load configuration
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"\n✅ Loaded configuration from {config_path}")

    # Create assistant
    print("\n🔧 Creating Voice Assistant...")
    assistant = VoiceAssistant(config)

    try:
        # Initialize all subsystems
        print("\n⚙️  Initializing subsystems...")
        await assistant.initialize()
        print("✅ Initialization complete")

        # Set status callback
        assistant.set_status_callback(status_callback)

        # Get initial status
        status = assistant.get_status()
        print(f"\n📊 Initial status: {status}")

        # Start the assistant
        print("\n🎤 Starting assistant (would normally listen for wake word)...")
        await assistant.start()

        # Simulate processing an audio event
        print("\n🎵 Simulating audio input...")

        # Generate dummy audio (2 seconds at 16kHz)
        sample_rate = 16000
        duration = 2.0
        num_samples = int(sample_rate * duration)
        audio_data = np.random.randint(-1000, 1000, num_samples, dtype=np.int16)

        # Create audio event
        import time
        audio_event = AudioEvent(
            type="hotkey",
            audio_data=audio_data,
            timestamp=time.time(),
            duration_seconds=duration,
        )

        # Process through pipeline
        # NOTE: This will fail without real STT/LLM, but demonstrates the flow
        try:
            print("\n🔄 Processing through pipeline...")
            result = await assistant.pipeline.process_audio_event(audio_event)

            if result.success:
                print(f"\n✅ Pipeline successful!")
                print(f"   Transcription: {result.transcription}")
                print(f"   Response: {result.response}")
                print(f"   Duration: {result.duration_ms:.1f}ms")
                print(f"   Tool calls: {result.tool_calls_made}")
            else:
                print(f"\n⚠️  Pipeline failed: {result.error}")

        except Exception as e:
            print(f"\n⚠️  Pipeline error (expected without real components): {e}")

        # Get metrics
        print("\n📈 Performance Metrics:")
        metrics = assistant.get_metrics()
        if metrics and metrics.get("system"):
            sys_metrics = metrics["system"]
            print(f"   Total requests: {sys_metrics.get('total_requests', 0)}")
            print(f"   Success rate: {sys_metrics.get('success_rate', 0) * 100:.1f}%")
            print(f"   Uptime: {sys_metrics.get('uptime_seconds', 0):.1f}s")

        # Get conversation info
        print("\n💬 Conversation Info:")
        conv_info = assistant.get_conversation_info()
        print(f"   Turns: {conv_info.get('turns_count', 0)}")
        print(f"   Messages: {conv_info.get('messages_count', 0)}")

        # Demonstrate conversation state
        print("\n💭 Conversation State:")
        if assistant.conversation_state:
            # Add a test exchange
            assistant.conversation_state.add_exchange(
                "What time is it?",
                "It's currently 3:45 PM",
            )

            messages = assistant.conversation_state.get_messages()
            print(f"   Total messages: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"   [{i}] {msg.role.value}: {msg.content[:50]}")

        # Demonstrate metrics
        print("\n📊 Metrics Collection:")
        if assistant.metrics:
            # Record some test metrics
            assistant.metrics.record_stage("test_stage", 100.0, success=True)
            assistant.metrics.record_stage("test_stage", 150.0, success=True)
            assistant.metrics.record_request(success=True, e2e_duration_ms=2500)

            stage_metrics = assistant.metrics.get_stage_metrics("test_stage")
            if stage_metrics:
                print(f"   Test stage avg: {stage_metrics.avg_duration_ms:.1f}ms")
                print(f"   Test stage calls: {stage_metrics.call_count}")

        # Wait a bit
        print("\n⏳ Running for 5 seconds...")
        await asyncio.sleep(5)

        # Stop the assistant
        print("\n🛑 Stopping assistant...")
        await assistant.stop()

        print(f"\n📊 Final status: {assistant.get_status()}")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await assistant.cleanup()
        print("✅ Cleanup complete")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
