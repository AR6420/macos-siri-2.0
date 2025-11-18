"""
Unit tests for CircularAudioBuffer
"""

import pytest
import numpy as np
from voice_assistant.audio.audio_buffer import CircularAudioBuffer


class TestCircularAudioBuffer:
    """Test suite for CircularAudioBuffer"""

    def test_initialization(self):
        """Test buffer initialization"""
        buffer = CircularAudioBuffer(
            duration_seconds=2.0,
            sample_rate=16000,
            channels=1
        )

        assert buffer.duration_seconds == 2.0
        assert buffer.sample_rate == 16000
        assert buffer.channels == 1
        assert buffer.buffer_size == 32000  # 2 * 16000 * 1
        assert not buffer.is_full
        assert buffer.write_index == 0

    def test_write_small_chunks(self):
        """Test writing small chunks of audio"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Write 100 samples
        chunk1 = np.arange(100, dtype=np.int16)
        buffer.write(chunk1)

        assert buffer.write_index == 100
        assert not buffer.is_full
        assert buffer.get_available_duration() == 0.1

    def test_write_wraparound(self):
        """Test buffer wraparound behavior"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Fill buffer
        chunk1 = np.arange(800, dtype=np.int16)
        buffer.write(chunk1)

        # Write more data to cause wraparound
        chunk2 = np.arange(800, 1000, dtype=np.int16)
        buffer.write(chunk2)

        assert buffer.is_full
        assert buffer.write_index == 0

    def test_read_chronological_order(self):
        """Test that read returns data in chronological order"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Write sequential data
        chunk1 = np.arange(0, 600, dtype=np.int16)
        buffer.write(chunk1)

        chunk2 = np.arange(600, 1200, dtype=np.int16)
        buffer.write(chunk2)

        # Buffer should be full and wrapped
        assert buffer.is_full

        # Read all data
        data = buffer.read_all()

        # Should get samples 200-1199 (most recent 1000 samples)
        expected = np.arange(200, 1200, dtype=np.int16)
        np.testing.assert_array_equal(data, expected)

    def test_read_before_full(self):
        """Test reading from buffer before it's full"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Write partial data
        chunk = np.arange(300, dtype=np.int16)
        buffer.write(chunk)

        # Read should return only available data
        data = buffer.read_all()
        assert len(data) == 300
        np.testing.assert_array_equal(data, chunk)

    def test_read_seconds(self):
        """Test reading specific duration"""
        buffer = CircularAudioBuffer(duration_seconds=2.0, sample_rate=1000)

        # Fill with data
        chunk = np.arange(2000, dtype=np.int16)
        buffer.write(chunk)

        # Read 0.5 seconds (500 samples)
        data = buffer.read_seconds(0.5)
        assert len(data) == 500

    def test_clear(self):
        """Test buffer clearing"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Fill buffer
        chunk = np.arange(1000, dtype=np.int16)
        buffer.write(chunk)

        # Clear
        buffer.clear()

        assert buffer.write_index == 0
        assert not buffer.is_full
        assert buffer.get_available_duration() == 0.0

    def test_large_write_exceeds_buffer(self):
        """Test writing data larger than buffer size"""
        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        # Write 2000 samples (larger than buffer)
        chunk = np.arange(2000, dtype=np.int16)
        buffer.write(chunk)

        # Should keep only the most recent 1000 samples
        assert buffer.is_full
        data = buffer.read_all()
        assert len(data) == 1000
        expected = np.arange(1000, 2000, dtype=np.int16)
        np.testing.assert_array_equal(data, expected)

    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading

        buffer = CircularAudioBuffer(duration_seconds=1.0, sample_rate=1000)

        def write_thread():
            for i in range(10):
                chunk = np.ones(100, dtype=np.int16) * i
                buffer.write(chunk)

        def read_thread():
            for _ in range(10):
                _ = buffer.read_all()

        # Start multiple threads
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=write_thread))
            threads.append(threading.Thread(target=read_thread))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should not crash or raise exceptions
        assert True

    def test_stereo_audio(self):
        """Test buffer with stereo audio"""
        buffer = CircularAudioBuffer(
            duration_seconds=1.0,
            sample_rate=1000,
            channels=2
        )

        # Buffer size should account for channels
        assert buffer.buffer_size == 2000  # 1.0 * 1000 * 2

        # Write stereo data
        chunk = np.arange(200, dtype=np.int16)  # 0.1 seconds of stereo
        buffer.write(chunk)

        assert buffer.get_available_duration() == 0.1

    def test_repr(self):
        """Test string representation"""
        buffer = CircularAudioBuffer(duration_seconds=3.0, sample_rate=16000)
        repr_str = repr(buffer)

        assert "CircularAudioBuffer" in repr_str
        assert "duration=3.0s" in repr_str
        assert "sample_rate=16000Hz" in repr_str
