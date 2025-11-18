"""
Test fixtures for audio data.

Provides realistic audio samples for testing different scenarios.
"""

import numpy as np
import wave
from pathlib import Path
from typing import Tuple


def generate_silence(duration_seconds: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Generate silent audio.

    Args:
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Audio samples as int16 array
    """
    num_samples = int(duration_seconds * sample_rate)
    return np.zeros(num_samples, dtype=np.int16)


def generate_tone(
    frequency: float = 440.0,
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.5,
) -> np.ndarray:
    """
    Generate a pure tone.

    Args:
        frequency: Frequency in Hz
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)

    Returns:
        Audio samples as int16 array
    """
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), endpoint=False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * amplitude * 32767).astype(np.int16)
    return audio


def generate_white_noise(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
    amplitude: float = 0.3,
) -> np.ndarray:
    """
    Generate white noise.

    Args:
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)

    Returns:
        Audio samples as int16 array
    """
    num_samples = int(duration_seconds * sample_rate)
    noise = np.random.randn(num_samples)
    noise = (noise * amplitude * 32767).astype(np.int16)
    return noise


def generate_speech_like(
    duration_seconds: float = 2.0,
    sample_rate: int = 16000,
    amplitude: float = 0.5,
) -> np.ndarray:
    """
    Generate synthetic speech-like audio.

    Creates audio with varying frequency content and amplitude envelope
    to simulate natural speech.

    Args:
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude (0.0 to 1.0)

    Returns:
        Audio samples as int16 array
    """
    num_samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, num_samples, endpoint=False)

    # Combine multiple frequencies (formants)
    f1 = 200 + 50 * np.sin(2 * np.pi * 3 * t)  # Varying fundamental
    f2 = 800 + 100 * np.sin(2 * np.pi * 2 * t)  # First formant
    f3 = 2500 + 200 * np.sin(2 * np.pi * 1.5 * t)  # Second formant

    audio = (
        0.4 * np.sin(2 * np.pi * f1 * t) +
        0.3 * np.sin(2 * np.pi * f2 * t) +
        0.2 * np.sin(2 * np.pi * f3 * t) +
        0.1 * np.random.randn(num_samples)  # Add noise
    )

    # Create amplitude envelope (simulates speech pauses)
    envelope = np.ones(num_samples)

    # Fade in
    fade_in_samples = int(0.1 * sample_rate)
    envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)

    # Fade out
    fade_out_samples = int(0.1 * sample_rate)
    envelope[-fade_out_samples:] = np.linspace(1, 0, fade_out_samples)

    # Add some pauses in the middle
    num_pauses = int(duration_seconds)
    for i in range(num_pauses):
        pause_start = int((i + 0.8) * sample_rate)
        pause_end = pause_start + int(0.1 * sample_rate)
        if pause_end < num_samples:
            envelope[pause_start:pause_end] *= 0.3

    audio = audio * envelope
    audio = (audio * amplitude * 32767).astype(np.int16)

    return audio


def generate_wake_word_audio(
    sample_rate: int = 16000,
) -> np.ndarray:
    """
    Generate synthetic "Hey Claude" wake word audio.

    Args:
        sample_rate: Sample rate in Hz

    Returns:
        Audio samples as int16 array
    """
    # "Hey" - about 0.3 seconds
    hey = generate_speech_like(duration_seconds=0.3, sample_rate=sample_rate, amplitude=0.6)

    # Pause - about 0.1 seconds
    pause = generate_silence(duration_seconds=0.1, sample_rate=sample_rate)

    # "Claude" - about 0.4 seconds
    claude = generate_speech_like(duration_seconds=0.4, sample_rate=sample_rate, amplitude=0.7)

    # Concatenate
    wake_word = np.concatenate([hey, pause, claude])

    return wake_word


def generate_command_audio(
    command_text: str,
    duration_seconds: float = 2.0,
    sample_rate: int = 16000,
) -> Tuple[np.ndarray, str]:
    """
    Generate synthetic command audio with associated text.

    Args:
        command_text: The text of the command
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz

    Returns:
        Tuple of (audio samples, command text)
    """
    # Estimate duration based on word count (rough approximation)
    word_count = len(command_text.split())
    estimated_duration = max(1.0, min(duration_seconds, word_count * 0.3))

    audio = generate_speech_like(
        duration_seconds=estimated_duration,
        sample_rate=sample_rate,
        amplitude=0.6,
    )

    return audio, command_text


def save_wav(
    audio: np.ndarray,
    filepath: Path,
    sample_rate: int = 16000,
    channels: int = 1,
) -> None:
    """
    Save audio to WAV file.

    Args:
        audio: Audio samples as int16 array
        filepath: Path to save file
        sample_rate: Sample rate in Hz
        channels: Number of channels
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())


def load_wav(filepath: Path) -> Tuple[np.ndarray, int]:
    """
    Load audio from WAV file.

    Args:
        filepath: Path to WAV file

    Returns:
        Tuple of (audio samples, sample rate)
    """
    with wave.open(str(filepath), 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16)

    return audio, sample_rate


# Pre-defined test scenarios
TEST_COMMANDS = [
    "What is the weather like today?",
    "Open Safari",
    "Send a message to John",
    "What time is it?",
    "Search for machine learning tutorials",
    "Create a new file called notes.txt",
    "Tell me a joke",
    "Set a timer for 5 minutes",
    "What's on my calendar today?",
    "Play some music",
]


def create_all_fixtures(output_dir: Path) -> None:
    """
    Create all audio test fixtures.

    Args:
        output_dir: Directory to save fixtures
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create silence
    save_wav(
        generate_silence(duration_seconds=2.0),
        output_dir / "silence_2s.wav"
    )

    # Create noise
    save_wav(
        generate_white_noise(duration_seconds=2.0),
        output_dir / "noise_2s.wav"
    )

    # Create wake word
    save_wav(
        generate_wake_word_audio(),
        output_dir / "wake_word_hey_claude.wav"
    )

    # Create test commands
    for i, command in enumerate(TEST_COMMANDS):
        audio, text = generate_command_audio(command)
        filename = f"command_{i:02d}_{command[:20].replace(' ', '_').lower()}.wav"
        save_wav(audio, output_dir / filename)

        # Also save the text
        text_file = output_dir / filename.replace('.wav', '.txt')
        text_file.write_text(text)

    # Create combined wake word + command samples
    for i, command in enumerate(TEST_COMMANDS[:5]):  # Just first 5
        wake = generate_wake_word_audio()
        pause = generate_silence(duration_seconds=0.2)
        cmd_audio, _ = generate_command_audio(command)

        combined = np.concatenate([wake, pause, cmd_audio])
        filename = f"full_{i:02d}_wakeword_plus_command.wav"
        save_wav(combined, output_dir / filename)

        # Save text
        text_file = output_dir / filename.replace('.wav', '.txt')
        text_file.write_text(f"Hey Claude {command}")

    print(f"✓ Created {len(list(output_dir.glob('*.wav')))} audio fixtures in {output_dir}")


if __name__ == "__main__":
    # Create fixtures when run directly
    fixtures_dir = Path(__file__).parent / "audio"
    create_all_fixtures(fixtures_dir)
