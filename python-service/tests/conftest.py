"""
Pytest configuration and shared fixtures
"""

import pytest
import numpy as np
from pathlib import Path


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require whisper.cpp installed)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow running"
    )


@pytest.fixture
def test_fixtures_dir():
    """Return path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_audio_file(test_fixtures_dir, tmp_path):
    """
    Create a sample WAV file for testing

    Returns path to WAV file
    """
    import wave

    # Generate 1 second of 440Hz tone
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 0.5 * 32767).astype(np.int16)

    # Save to WAV
    wav_path = tmp_path / "test_audio.wav"
    with wave.open(str(wav_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

    return wav_path


@pytest.fixture
def silence_audio():
    """Generate 1 second of silence"""
    sample_rate = 16000
    duration = 1.0
    return np.zeros(int(sample_rate * duration), dtype=np.int16)


@pytest.fixture
def speech_audio():
    """Generate synthetic speech-like audio"""
    sample_rate = 16000
    duration = 2.0

    # Create varying frequency content to simulate speech
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Combine multiple frequencies
    audio = (
        0.3 * np.sin(2 * np.pi * 200 * t) +
        0.3 * np.sin(2 * np.pi * 400 * t) +
        0.2 * np.sin(2 * np.pi * 800 * t) +
        0.1 * np.random.randn(len(t))  # Add noise
    )

    # Apply amplitude envelope (simulates speech segments)
    envelope = np.ones_like(t)
    envelope[:1000] *= np.linspace(0, 1, 1000)  # Fade in
    envelope[-1000:] *= np.linspace(1, 0, 1000)  # Fade out

    audio = audio * envelope
    audio = (audio * 0.3 * 32767).astype(np.int16)

    return audio
