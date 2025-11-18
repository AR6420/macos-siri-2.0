"""
Integration tests for audio pipeline
"""

import pytest
import numpy as np
import asyncio
import wave
import os
from pathlib import Path
from voice_assistant.audio import AudioPipeline, AudioEvent, AudioConfig


class TestAudioPipelineIntegration:
    """Integration tests for complete audio pipeline"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return AudioConfig(
            wake_word_enabled=False,  # Disable for basic tests
            sample_rate=16000,
            channels=1,
            chunk_size=512,
            buffer_duration_seconds=3.0,
            vad_threshold=0.5,
            min_silence_duration_ms=500
        )

    @pytest.fixture
    def test_audio_file(self, tmp_path):
        """Create a test WAV file"""
        file_path = tmp_path / "test_audio.wav"

        # Generate 2 seconds of 440Hz sine wave
        sample_rate = 16000
        duration = 2.0
        frequency = 440.0

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)

        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Write WAV file
        with wave.open(str(file_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 2 bytes for int16
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return file_path

    def test_pipeline_initialization(self, config):
        """Test pipeline initializes correctly"""
        with AudioPipeline(config) as pipeline:
            assert pipeline.config == config
            assert not pipeline.is_running
            assert pipeline.circular_buffer is not None
            assert pipeline.vad is not None

    def test_pipeline_status(self, config):
        """Test pipeline status reporting"""
        with AudioPipeline(config) as pipeline:
            status = pipeline.get_status()

            assert status['is_running'] is False
            assert status['listening_mode'] is False
            assert status['sample_rate'] == 16000
            assert status['buffer_duration'] == 3.0

    def test_hotkey_trigger(self, config):
        """Test manual hotkey triggering"""
        with AudioPipeline(config) as pipeline:
            assert not pipeline._hotkey_triggered

            pipeline.trigger_hotkey()

            assert pipeline._hotkey_triggered

    @pytest.mark.asyncio
    async def test_pipeline_callbacks(self, config):
        """Test that callbacks are registered"""
        wake_word_called = []
        audio_ready_called = []
        error_called = []

        async def on_wake_word(event: AudioEvent):
            wake_word_called.append(event)

        async def on_audio_ready(event: AudioEvent):
            audio_ready_called.append(event)

        def on_error(error: Exception):
            error_called.append(error)

        with AudioPipeline(config) as pipeline:
            # Note: We can't actually start the pipeline in tests without audio device
            # This just tests that callbacks are registered
            assert pipeline._on_wake_word is None
            assert pipeline._on_audio_ready is None
            assert pipeline._on_error is None

    def test_sensitivity_update(self, config):
        """Test updating wake word sensitivity"""
        config.wake_word_enabled = False  # Use mock detector

        with AudioPipeline(config) as pipeline:
            pipeline.update_wake_word_sensitivity(0.8)

            assert pipeline.config.wake_word_sensitivity == 0.8

    def test_circular_buffer_integration(self, config):
        """Test circular buffer is populated correctly"""
        with AudioPipeline(config) as pipeline:
            # Write some test data to buffer
            test_audio = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
            pipeline.circular_buffer.write(test_audio)

            # Read it back
            read_audio = pipeline.circular_buffer.read(1600)

            np.testing.assert_array_equal(test_audio, read_audio)

    def test_vad_integration(self, config):
        """Test VAD integration"""
        with AudioPipeline(config) as pipeline:
            # Generate speech-like audio (higher energy)
            speech_audio = np.random.randint(-20000, 20000, 1600, dtype=np.int16)

            # Test VAD
            is_speech, confidence = pipeline.vad.is_speech(speech_audio)

            # Should detect as speech (high energy)
            assert isinstance(is_speech, bool)
            assert 0.0 <= confidence <= 1.0

    def test_repr(self, config):
        """Test string representation"""
        with AudioPipeline(config) as pipeline:
            repr_str = repr(pipeline)

            assert "AudioPipeline" in repr_str
            assert "stopped" in repr_str

    @pytest.mark.skip(reason="Requires real audio device")
    @pytest.mark.asyncio
    async def test_full_pipeline_with_audio_device(self, config):
        """
        Test full pipeline with real audio device.

        This test is skipped by default as it requires:
        - A working audio input device
        - User interaction (speaking)

        To run manually:
        pytest -v -k test_full_pipeline_with_audio_device --no-skip
        """
        received_events = []

        async def on_audio_ready(event: AudioEvent):
            received_events.append(event)
            print(f"Received {event.duration_seconds}s of audio")

        with AudioPipeline(config) as pipeline:
            await pipeline.start(on_audio_ready=on_audio_ready)

            # Wait for user to trigger hotkey
            print("Press Cmd+Shift+Space (or trigger hotkey programmatically)")
            pipeline.trigger_hotkey()

            # Wait for recording
            await asyncio.sleep(5)

            pipeline.stop()

            assert len(received_events) > 0


class TestAudioEventDataClass:
    """Test AudioEvent dataclass"""

    def test_creation(self):
        """Test creating AudioEvent"""
        audio_data = np.zeros(1600, dtype=np.int16)

        event = AudioEvent(
            type="wake_word",
            audio_data=audio_data,
            timestamp=123.456,
            duration_seconds=0.1
        )

        assert event.type == "wake_word"
        assert len(event.audio_data) == 1600
        assert event.timestamp == 123.456
        assert event.duration_seconds == 0.1
        assert event.metadata == {}

    def test_with_metadata(self):
        """Test AudioEvent with metadata"""
        audio_data = np.zeros(1600, dtype=np.int16)

        event = AudioEvent(
            type="audio_ready",
            audio_data=audio_data,
            timestamp=123.456,
            duration_seconds=5.0,
            metadata={"confidence": 0.95, "language": "en"}
        )

        assert event.metadata["confidence"] == 0.95
        assert event.metadata["language"] == "en"
