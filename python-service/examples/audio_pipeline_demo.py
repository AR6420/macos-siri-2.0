#!/usr/bin/env python3
"""
Audio Pipeline Demo

Demonstrates basic usage of the audio pipeline for wake word detection
and audio capture.

Usage:
    python audio_pipeline_demo.py

Requirements:
    - Porcupine access key (set PORCUPINE_ACCESS_KEY env var)
    - Working microphone
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_assistant.audio import AudioPipeline, AudioEvent, AudioConfig
import numpy as np


async def on_wake_word(event: AudioEvent) -> None:
    """Called when wake word is detected"""
    print(f"\n🎤 Wake word detected! (trigger: {event.metadata.get('trigger', 'unknown')})")
    print(f"   Buffered audio: {event.duration_seconds:.2f}s")


async def on_audio_ready(event: AudioEvent) -> None:
    """Called when complete utterance is ready"""
    print(f"\n✅ Audio ready for processing!")
    print(f"   Duration: {event.duration_seconds:.2f}s")
    print(f"   Samples: {len(event.audio_data)}")
    print(f"   Sample rate: {event.metadata.get('sample_rate', 16000)}Hz")

    # Calculate RMS energy to show audio quality
    audio_float = event.audio_data.astype(np.float32) / 32768.0
    rms = np.sqrt(np.mean(audio_float ** 2))
    print(f"   RMS energy: {rms:.4f}")

    # In a real application, you would send this to STT here
    print(f"   → Next step: Send to Whisper for transcription")


def on_error(error: Exception) -> None:
    """Called when an error occurs"""
    print(f"\n❌ Error: {error}")


async def main():
    """Main demo function"""
    print("=" * 60)
    print("Audio Pipeline Demo")
    print("=" * 60)

    # Get Porcupine access key from environment
    access_key = os.getenv("PORCUPINE_ACCESS_KEY", "")

    if not access_key:
        print("\n⚠️  PORCUPINE_ACCESS_KEY not set!")
        print("   Get your key from: https://console.picovoice.ai/")
        print("   Then: export PORCUPINE_ACCESS_KEY='your-key-here'")
        print("\n   Continuing with mock wake word detector (no detection)...\n")

    # Create configuration
    config = AudioConfig(
        wake_word_enabled=True,
        wake_word_access_key=access_key,
        wake_word_sensitivity=0.5,
        sample_rate=16000,
        channels=1,
        buffer_duration_seconds=3.0,
        vad_threshold=0.5,
        min_silence_duration_ms=800,  # Wait 800ms of silence before ending
        max_utterance_seconds=30.0
    )

    print("\nConfiguration:")
    print(f"  Sample rate: {config.sample_rate}Hz")
    print(f"  Buffer duration: {config.buffer_duration_seconds}s")
    print(f"  Wake word sensitivity: {config.wake_word_sensitivity}")
    print(f"  VAD threshold: {config.vad_threshold}")
    print(f"  Min silence: {config.min_silence_duration_ms}ms")

    # Create and start pipeline
    with AudioPipeline(config) as pipeline:
        print("\n🎙️  Starting audio pipeline...")

        try:
            await pipeline.start(
                on_wake_word=on_wake_word,
                on_audio_ready=on_audio_ready,
                on_error=on_error
            )

            status = pipeline.get_status()
            print(f"\n✓ Pipeline started!")
            print(f"  Device: {status['device']}")
            print(f"  Status: {status['is_running']}")

            if access_key:
                print("\n💡 Say 'Hey Claude' to trigger (or press Ctrl+C to use hotkey)")
            else:
                print("\n💡 Wake word detection disabled - using hotkey mode only")

            print("\n📝 Instructions:")
            print("  1. Trigger with wake word OR call pipeline.trigger_hotkey()")
            print("  2. Speak your command")
            print("  3. Wait for VAD to detect silence (or 30s timeout)")
            print("  4. Audio will be processed\n")

            # Demo: Trigger via hotkey after 3 seconds
            print("⏱️  In 3 seconds, will trigger via hotkey...")
            await asyncio.sleep(3)

            print("\n🔥 Triggering hotkey! Speak now...")
            pipeline.trigger_hotkey()

            # Keep running
            while True:
                await asyncio.sleep(1)

                # Check if we want to trigger again (for demo purposes)
                # In real app, this would be connected to actual hotkey listener

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping pipeline...")
            pipeline.stop()

        print("✅ Pipeline stopped cleanly")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
