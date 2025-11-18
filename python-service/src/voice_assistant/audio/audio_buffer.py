"""
Circular Audio Buffer Implementation

Maintains a fixed-size rolling buffer of recent audio data to capture
pre-wake-word audio context.
"""

import numpy as np
from typing import Optional
import threading


class CircularAudioBuffer:
    """
    Thread-safe circular buffer for audio data.

    Maintains a rolling window of recent audio samples to enable
    capturing context before wake word detection.

    Attributes:
        duration_seconds: Buffer duration in seconds
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels
    """

    def __init__(
        self,
        duration_seconds: float = 3.0,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype=np.int16
    ):
        """
        Initialize circular buffer.

        Args:
            duration_seconds: How many seconds of audio to buffer
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
            dtype: NumPy data type for audio samples
        """
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype

        # Calculate buffer size in samples
        self.buffer_size = int(duration_seconds * sample_rate * channels)

        # Initialize circular buffer
        self.buffer = np.zeros(self.buffer_size, dtype=dtype)
        self.write_index = 0
        self.is_full = False

        # Thread safety
        self._lock = threading.Lock()

    def write(self, audio_data: np.ndarray) -> None:
        """
        Write audio data to the circular buffer.

        Args:
            audio_data: Audio samples to write (1D array)
        """
        with self._lock:
            num_samples = len(audio_data)

            # Handle case where data is larger than buffer
            if num_samples >= self.buffer_size:
                # Just keep the most recent buffer_size samples
                self.buffer[:] = audio_data[-self.buffer_size:]
                self.write_index = 0
                self.is_full = True
                return

            # Calculate how much space is available before wraparound
            space_to_end = self.buffer_size - self.write_index

            if num_samples <= space_to_end:
                # Data fits before end of buffer
                self.buffer[self.write_index:self.write_index + num_samples] = audio_data
                self.write_index = (self.write_index + num_samples) % self.buffer_size
            else:
                # Data wraps around to beginning
                self.buffer[self.write_index:] = audio_data[:space_to_end]
                remaining = num_samples - space_to_end
                self.buffer[:remaining] = audio_data[space_to_end:]
                self.write_index = remaining

            # Mark buffer as full once we've wrapped around
            if self.write_index == 0 or num_samples > space_to_end:
                self.is_full = True

    def read(self, num_samples: Optional[int] = None) -> np.ndarray:
        """
        Read audio data from the buffer in chronological order.

        Args:
            num_samples: Number of samples to read. If None, reads entire buffer.

        Returns:
            Audio data in chronological order (oldest first)
        """
        with self._lock:
            if num_samples is None:
                num_samples = self.buffer_size

            # Clamp to buffer size
            num_samples = min(num_samples, self.buffer_size)

            if not self.is_full:
                # Buffer not full yet, return what we have
                available = self.write_index
                num_samples = min(num_samples, available)
                return self.buffer[:num_samples].copy()

            # Buffer is full, read in chronological order
            # Oldest data is at write_index, newest is at write_index - 1
            result = np.zeros(num_samples, dtype=self.dtype)

            if num_samples <= self.buffer_size - self.write_index:
                # All data is contiguous after write_index
                result[:] = self.buffer[self.write_index:self.write_index + num_samples]
            else:
                # Data wraps around
                first_chunk_size = self.buffer_size - self.write_index
                result[:first_chunk_size] = self.buffer[self.write_index:]
                remaining = num_samples - first_chunk_size
                result[first_chunk_size:] = self.buffer[:remaining]

            return result

    def read_all(self) -> np.ndarray:
        """
        Read all available audio data in chronological order.

        Returns:
            All buffered audio data (oldest first)
        """
        return self.read()

    def read_seconds(self, seconds: float) -> np.ndarray:
        """
        Read specified duration of audio from the buffer.

        Args:
            seconds: Duration to read in seconds

        Returns:
            Audio data for the specified duration
        """
        num_samples = int(seconds * self.sample_rate * self.channels)
        return self.read(num_samples)

    def clear(self) -> None:
        """Clear the buffer and reset to initial state."""
        with self._lock:
            self.buffer.fill(0)
            self.write_index = 0
            self.is_full = False

    def get_available_duration(self) -> float:
        """
        Get the duration of audio currently in the buffer.

        Returns:
            Duration in seconds
        """
        with self._lock:
            if self.is_full:
                return self.duration_seconds
            else:
                return self.write_index / (self.sample_rate * self.channels)

    def __len__(self) -> int:
        """Return number of samples currently in buffer."""
        with self._lock:
            return self.buffer_size if self.is_full else self.write_index

    def __repr__(self) -> str:
        return (
            f"CircularAudioBuffer(duration={self.duration_seconds}s, "
            f"sample_rate={self.sample_rate}Hz, channels={self.channels}, "
            f"available={self.get_available_duration():.2f}s)"
        )
