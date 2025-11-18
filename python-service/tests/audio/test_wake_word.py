"""
Unit tests for WakeWordDetector
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from voice_assistant.audio.wake_word import WakeWordDetector, MockWakeWordDetector


class TestMockWakeWordDetector:
    """Test mock wake word detector"""

    def test_initialization(self):
        """Test mock detector initialization"""
        detector = MockWakeWordDetector(sensitivity=0.7)

        assert detector.sample_rate == 16000
        assert detector.frame_length == 512
        assert detector.sensitivity == 0.7

    def test_process_frame_always_false(self):
        """Test that mock detector never detects wake word"""
        detector = MockWakeWordDetector()

        audio_frame = np.random.randint(-32768, 32767, 512, dtype=np.int16)
        result = detector.process_frame(audio_frame)

        assert result is False

    def test_process_audio_always_empty(self):
        """Test that mock detector returns no detections"""
        detector = MockWakeWordDetector()

        audio_data = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
        detections = detector.process_audio(audio_data)

        assert detections == []

    def test_context_manager(self):
        """Test mock detector as context manager"""
        with MockWakeWordDetector() as detector:
            assert detector is not None

    def test_update_sensitivity(self):
        """Test sensitivity update"""
        detector = MockWakeWordDetector()
        detector.update_sensitivity(0.9)

        assert detector.sensitivity == 0.9


@pytest.mark.skipif(
    not pytest.importorskip("pvporcupine", minversion=None),
    reason="pvporcupine not installed"
)
class TestWakeWordDetector:
    """Test real wake word detector (requires pvporcupine)"""

    @pytest.fixture
    def mock_porcupine(self):
        """Mock Porcupine instance"""
        with patch('voice_assistant.audio.wake_word.pvporcupine') as mock_pv:
            mock_instance = Mock()
            mock_instance.sample_rate = 16000
            mock_instance.frame_length = 512
            mock_instance.process.return_value = -1  # No detection

            mock_pv.create.return_value = mock_instance
            yield mock_pv, mock_instance

    def test_initialization_no_access_key(self):
        """Test that initialization fails without access key"""
        with pytest.raises(ValueError, match="access_key is required"):
            WakeWordDetector(access_key="")

    def test_initialization_invalid_sensitivity(self):
        """Test that initialization fails with invalid sensitivity"""
        with pytest.raises(ValueError, match="Sensitivity must be between"):
            WakeWordDetector(access_key="test_key", sensitivity=1.5)

        with pytest.raises(ValueError, match="Sensitivity must be between"):
            WakeWordDetector(access_key="test_key", sensitivity=-0.1)

    def test_initialization_with_mock(self, mock_porcupine):
        """Test initialization with mocked Porcupine"""
        mock_pv, mock_instance = mock_porcupine

        detector = WakeWordDetector(
            access_key="test_key",
            sensitivity=0.6
        )

        assert detector.sample_rate == 16000
        assert detector.frame_length == 512
        assert detector.sensitivity == 0.6

    def test_process_frame_no_detection(self, mock_porcupine):
        """Test processing frame without detection"""
        mock_pv, mock_instance = mock_porcupine
        mock_instance.process.return_value = -1

        detector = WakeWordDetector(access_key="test_key")

        audio_frame = np.zeros(512, dtype=np.int16)
        result = detector.process_frame(audio_frame)

        assert result is False
        mock_instance.process.assert_called_once()

    def test_process_frame_with_detection(self, mock_porcupine):
        """Test processing frame with detection"""
        mock_pv, mock_instance = mock_porcupine
        mock_instance.process.return_value = 0  # Detection!

        detector = WakeWordDetector(access_key="test_key")

        audio_frame = np.zeros(512, dtype=np.int16)
        result = detector.process_frame(audio_frame)

        assert result is True

    def test_process_frame_wrong_length(self, mock_porcupine):
        """Test processing frame with incorrect length"""
        mock_pv, mock_instance = mock_porcupine

        detector = WakeWordDetector(access_key="test_key")

        audio_frame = np.zeros(256, dtype=np.int16)  # Wrong length

        with pytest.raises(ValueError, match="must be 512 samples"):
            detector.process_frame(audio_frame)

    def test_process_audio_multiple_frames(self, mock_porcupine):
        """Test processing multiple frames"""
        mock_pv, mock_instance = mock_porcupine
        # Simulate detection on second frame
        mock_instance.process.side_effect = [-1, 0, -1]

        detector = WakeWordDetector(access_key="test_key")

        # 3 frames worth of audio
        audio_data = np.zeros(512 * 3, dtype=np.int16)
        detections = detector.process_audio(audio_data)

        assert len(detections) == 1
        assert detections[0] == 512  # Second frame starts at index 512

    def test_detection_callback(self, mock_porcupine):
        """Test detection callback is called"""
        mock_pv, mock_instance = mock_porcupine
        mock_instance.process.return_value = 0  # Detection

        detector = WakeWordDetector(access_key="test_key", sensitivity=0.7)

        callback_called = []

        def callback(sensitivity):
            callback_called.append(sensitivity)

        detector.set_detection_callback(callback)

        audio_frame = np.zeros(512, dtype=np.int16)
        detector.process_frame(audio_frame)

        assert len(callback_called) == 1
        assert callback_called[0] == 0.7

    def test_context_manager(self, mock_porcupine):
        """Test detector as context manager"""
        mock_pv, mock_instance = mock_porcupine

        with WakeWordDetector(access_key="test_key") as detector:
            assert detector is not None

        # Should call delete on exit
        mock_instance.delete.assert_called_once()

    def test_close(self, mock_porcupine):
        """Test explicit close"""
        mock_pv, mock_instance = mock_porcupine

        detector = WakeWordDetector(access_key="test_key")
        detector.close()

        mock_instance.delete.assert_called_once()

    def test_repr(self, mock_porcupine):
        """Test string representation"""
        mock_pv, mock_instance = mock_porcupine

        detector = WakeWordDetector(access_key="test_key", sensitivity=0.6)
        repr_str = repr(detector)

        assert "WakeWordDetector" in repr_str
        assert "sensitivity=0.6" in repr_str
        assert "16000Hz" in repr_str
