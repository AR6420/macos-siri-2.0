#!/usr/bin/env python3
"""
Example usage of Speech-to-Text module

This script demonstrates how to use the WhisperSTT client
to transcribe audio files or numpy arrays.
"""

import sys
import numpy as np
import wave
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_assistant.stt import (
    WhisperSTT,
    AudioInput,
    WhisperModel,
    ModelManager,
)


def load_wav_file(filepath: Path) -> AudioInput:
    """
    Load audio from WAV file

    Args:
        filepath: Path to WAV file

    Returns:
        AudioInput object
    """
    with wave.open(str(filepath), 'rb') as wav_file:
        # Get audio parameters
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())

        # Convert to numpy array
        audio = np.frombuffer(frames, dtype=np.int16)

        # Convert stereo to mono if needed
        if channels == 2:
            audio = audio.reshape(-1, 2)
            audio = audio.mean(axis=1).astype(np.int16)

        return AudioInput(
            samples=audio,
            sample_rate=sample_rate,
            language="en"
        )


def example_transcribe_wav(wav_path: str):
    """
    Example: Transcribe a WAV file

    Args:
        wav_path: Path to WAV file
    """
    print("=" * 60)
    print("Example 1: Transcribe WAV file")
    print("=" * 60)
    print(f"Input file: {wav_path}")
    print()

    # Load audio
    audio = load_wav_file(Path(wav_path))
    print(f"Loaded audio: {len(audio.samples)} samples at {audio.sample_rate}Hz")
    print()

    # Create STT client
    stt = WhisperSTT(
        model=WhisperModel.SMALL_EN,
        enable_cache=True,
        enable_vad=True,
    )

    # Transcribe
    print("Transcribing...")
    result = stt.transcribe(audio)

    # Print results
    print()
    print("Results:")
    print(f"  Text: {result.text}")
    print(f"  Language: {result.language}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Duration: {result.duration_ms}ms")
    print(f"  Model: {result.model_used}")
    print(f"  Cache hit: {result.cache_hit}")
    print()


def example_transcribe_numpy():
    """
    Example: Transcribe numpy audio array
    """
    print("=" * 60)
    print("Example 2: Transcribe numpy array (generated audio)")
    print("=" * 60)
    print()

    # Generate sample audio (1 second of 440Hz tone)
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 0.5 * 32767).astype(np.int16)

    audio_input = AudioInput(
        samples=audio,
        sample_rate=sample_rate,
        language="en"
    )

    print(f"Generated audio: {len(audio)} samples at {sample_rate}Hz")
    print()

    # Create STT client (disable VAD for tone)
    stt = WhisperSTT(
        model=WhisperModel.SMALL_EN,
        enable_cache=False,
        enable_vad=False,
    )

    # Transcribe
    print("Transcribing...")
    result = stt.transcribe(audio_input)

    # Print results
    print()
    print("Results:")
    print(f"  Text: {result.text if result.text else '(no speech detected)'}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Duration: {result.duration_ms}ms")
    print()


def example_model_management():
    """
    Example: Model management operations
    """
    print("=" * 60)
    print("Example 3: Model Management")
    print("=" * 60)
    print()

    manager = ModelManager()

    # List available models
    print("Available models:")
    print()

    for model, has_base, has_coreml in manager.list_available_models():
        info = manager.get_model_info(model)
        status = []
        if has_base:
            status.append("downloaded")
        if has_coreml:
            status.append("CoreML")

        status_str = ", ".join(status) if status else "not downloaded"

        print(f"  {model.value:12} - {info['size_mb']:4}MB - {status_str}")
        print(f"                {info['description']}")
        print()

    # Check whisper.cpp installation
    print()
    print("Whisper.cpp installation:")
    if manager.verify_whisper_cpp_installation():
        print(f"  ✓ Installed at: {manager.whisper_cpp_path}")
    else:
        print(f"  ✗ Not found at: {manager.whisper_cpp_path}")
        print(f"  Run: scripts/setup_whisper.sh")
    print()


async def example_async_transcription(wav_path: str):
    """
    Example: Async transcription

    Args:
        wav_path: Path to WAV file
    """
    print("=" * 60)
    print("Example 4: Async Transcription")
    print("=" * 60)
    print()

    # Load audio
    audio = load_wav_file(Path(wav_path))

    # Create STT client
    stt = WhisperSTT(
        model=WhisperModel.SMALL_EN,
        enable_cache=True,
    )

    # Transcribe asynchronously
    print("Transcribing asynchronously...")
    result = await stt.transcribe_async(audio)

    print()
    print("Results:")
    print(f"  Text: {result.text}")
    print(f"  Duration: {result.duration_ms}ms")
    print()


def example_audio_preprocessing():
    """
    Example: Audio preprocessing
    """
    print("=" * 60)
    print("Example 5: Audio Preprocessing")
    print("=" * 60)
    print()

    from voice_assistant.stt.audio_processor import AudioProcessor

    processor = AudioProcessor()

    # Generate sample audio with silence
    sample_rate = 16000
    silence1 = np.zeros(int(sample_rate * 0.5))
    speech = np.random.randn(int(sample_rate * 1.0)) * 0.3
    silence2 = np.zeros(int(sample_rate * 0.5))

    audio = np.concatenate([silence1, speech, silence2]).astype(np.float32)

    print(f"Original audio: {len(audio)} samples ({len(audio)/sample_rate:.1f}s)")
    print()

    # Detect speech
    segments = processor.detect_speech_segments(audio, sample_rate)
    print(f"Detected {len(segments)} speech segments:")
    for i, (start, end) in enumerate(segments):
        duration = (end - start) / sample_rate
        print(f"  Segment {i+1}: {start}-{end} ({duration:.2f}s)")
    print()

    # Extract speech
    speech_only = processor.extract_speech(audio, sample_rate)
    print(f"Extracted speech: {len(speech_only)} samples ({len(speech_only)/sample_rate:.1f}s)")
    print()

    # Normalize
    normalized = processor.normalize_audio(audio)
    print(f"Normalized audio: min={normalized.min():.3f}, max={normalized.max():.3f}")
    print()


def main():
    """Run examples"""
    import argparse

    parser = argparse.ArgumentParser(description="STT module examples")
    parser.add_argument(
        "--wav",
        type=str,
        help="Path to WAV file for transcription examples"
    )
    parser.add_argument(
        "--example",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run specific example (1-5)"
    )

    args = parser.parse_args()

    try:
        if args.example == 1 or (args.wav and not args.example):
            if not args.wav:
                print("Error: --wav required for example 1")
                return
            example_transcribe_wav(args.wav)

        elif args.example == 2:
            example_transcribe_numpy()

        elif args.example == 3:
            example_model_management()

        elif args.example == 4:
            if not args.wav:
                print("Error: --wav required for example 4")
                return
            import asyncio
            asyncio.run(example_async_transcription(args.wav))

        elif args.example == 5:
            example_audio_preprocessing()

        else:
            # Run all non-file examples
            example_transcribe_numpy()
            example_model_management()
            example_audio_preprocessing()

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
