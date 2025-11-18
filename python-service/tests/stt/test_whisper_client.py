"""
Tests for Whisper STT Client
"""

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from voice_assistant.stt import (
    WhisperSTT,
    AudioInput,
    TranscriptionResult,
    WhisperModel,
    ModelManager,
)


@pytest.fixture
def sample_audio():
    """Generate sample audio data (1 second of 440Hz tone)"""
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 0.5 * 32767).astype(np.int16)

    return AudioInput(samples=audio, sample_rate=sample_rate, language="en")


@pytest.fixture
def mock_whisper_cpp(tmp_path):
    """Mock whisper.cpp executable"""
    whisper_path = tmp_path / "whisper"
    whisper_path.write_text("#!/bin/bash\necho 'Hello world'\n")
    whisper_path.chmod(0o755)
    return whisper_path


class TestAudioInput:
    """Test AudioInput dataclass"""

    def test_valid_audio_input(self):
        """Test valid audio input creation"""
        audio = np.zeros(16000, dtype=np.int16)
        input_data = AudioInput(samples=audio, sample_rate=16000)

        assert input_data.sample_rate == 16000
        assert input_data.language == "en"
        assert len(input_data.samples) == 16000

    def test_invalid_sample_rate(self):
        """Test invalid sample rate raises error"""
        audio = np.zeros(16000, dtype=np.int16)

        with pytest.raises(ValueError, match="Unsupported sample rate"):
            AudioInput(samples=audio, sample_rate=12345)

    def test_stereo_audio_rejected(self):
        """Test stereo audio is rejected"""
        audio = np.zeros((16000, 2), dtype=np.int16)

        with pytest.raises(ValueError, match="must be mono"):
            AudioInput(samples=audio, sample_rate=16000)


class TestTranscriptionResult:
    """Test TranscriptionResult dataclass"""

    def test_result_creation(self):
        """Test result creation and text cleanup"""
        result = TranscriptionResult(
            text="  Hello world  ",
            language="en",
            confidence=0.95,
            duration_ms=500,
        )

        assert result.text == "Hello world"  # Trimmed
        assert result.confidence == 0.95
        assert result.duration_ms == 500

    def test_default_segments(self):
        """Test default empty segments list"""
        result = TranscriptionResult(
            text="Test",
            language="en",
            confidence=0.9,
            duration_ms=100,
        )

        assert result.segments == []


class TestWhisperSTT:
    """Test WhisperSTT client"""

    @patch('voice_assistant.stt.whisper_client.ModelManager')
    def test_initialization(self, mock_model_manager, tmp_path):
        """Test WhisperSTT initialization"""
        # Setup mock
        mock_manager_instance = Mock()
        mock_manager_instance.whisper_cpp_path = tmp_path / "whisper"
        mock_manager_instance.whisper_cpp_path.exists = Mock(return_value=True)
        mock_manager_instance.get_model_path = Mock(
            return_value=tmp_path / "model.bin"
        )
        mock_model_manager.return_value = mock_manager_instance

        # Create model file
        (tmp_path / "model.bin").touch()

        stt = WhisperSTT(
            whisper_cpp_path=tmp_path / "whisper",
            model=WhisperModel.SMALL_EN,
            enable_cache=False,
        )

        assert stt.model == WhisperModel.SMALL_EN
        assert stt.language == "en"
        assert stt.enable_cache == False

    def test_cache_key_generation(self, tmp_path, sample_audio):
        """Test cache key generation is consistent"""
        with patch('voice_assistant.stt.whisper_client.ModelManager'):
            stt = WhisperSTT(
                whisper_cpp_path=tmp_path / "whisper",
                enable_cache=True,
                cache_dir=tmp_path / "cache",
            )

            key1 = stt._get_cache_key(sample_audio)
            key2 = stt._get_cache_key(sample_audio)

            assert key1 == key2
            assert len(key1) == 64  # SHA256 hex

    def test_wav_file_creation(self, tmp_path, sample_audio):
        """Test WAV file creation from numpy array"""
        with patch('voice_assistant.stt.whisper_client.ModelManager'):
            stt = WhisperSTT(
                whisper_cpp_path=tmp_path / "whisper",
                enable_cache=False,
            )

            wav_path = tmp_path / "test.wav"
            stt._save_audio_to_wav(
                sample_audio.samples,
                sample_audio.sample_rate,
                wav_path
            )

            assert wav_path.exists()
            assert wav_path.stat().st_size > 0

    def test_float32_to_int16_conversion(self, tmp_path):
        """Test float32 audio conversion to int16"""
        with patch('voice_assistant.stt.whisper_client.ModelManager'):
            stt = WhisperSTT(
                whisper_cpp_path=tmp_path / "whisper",
                enable_cache=False,
            )

            # Create float32 audio
            audio_float = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)

            wav_path = tmp_path / "test.wav"
            stt._save_audio_to_wav(audio_float, 16000, wav_path)

            assert wav_path.exists()

    @patch('voice_assistant.stt.whisper_client.ModelManager')
    @patch('voice_assistant.stt.whisper_client.subprocess.run')
    def test_execute_whisper_cpp(self, mock_run, mock_model_manager, tmp_path):
        """Test whisper.cpp execution"""
        # Setup mocks
        mock_manager_instance = Mock()
        mock_manager_instance.whisper_cpp_path = tmp_path / "whisper"
        mock_manager_instance.get_model_path = Mock(
            return_value=tmp_path / "model.bin"
        )
        mock_manager_instance.has_coreml_model = Mock(return_value=False)
        mock_model_manager.return_value = mock_manager_instance

        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr="whisper_init_from_file_no_state\nprocessing\nHello world\n",
        )

        stt = WhisperSTT(
            whisper_cpp_path=tmp_path / "whisper",
            enable_cache=False,
        )

        # Create dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.touch()

        result = stt._execute_whisper_cpp(audio_file, "en")

        assert result['success'] == True
        assert "Hello world" in result['text']
        mock_run.assert_called_once()

    @patch('voice_assistant.stt.whisper_client.ModelManager')
    @patch('voice_assistant.stt.whisper_client.subprocess.run')
    def test_execute_whisper_timeout(self, mock_run, mock_model_manager, tmp_path):
        """Test whisper.cpp timeout handling"""
        # Setup mocks
        mock_manager_instance = Mock()
        mock_manager_instance.whisper_cpp_path = tmp_path / "whisper"
        mock_manager_instance.get_model_path = Mock(
            return_value=tmp_path / "model.bin"
        )
        mock_manager_instance.has_coreml_model = Mock(return_value=False)
        mock_model_manager.return_value = mock_manager_instance

        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("whisper", 30)

        stt = WhisperSTT(
            whisper_cpp_path=tmp_path / "whisper",
            enable_cache=False,
        )

        audio_file = tmp_path / "test.wav"
        audio_file.touch()

        result = stt._execute_whisper_cpp(audio_file, "en")

        assert result['success'] == False
        assert result['error'] == 'timeout'

    def test_cache_save_and_load(self, tmp_path, sample_audio):
        """Test cache save and load functionality"""
        with patch('voice_assistant.stt.whisper_client.ModelManager'):
            stt = WhisperSTT(
                whisper_cpp_path=tmp_path / "whisper",
                enable_cache=True,
                cache_dir=tmp_path / "cache",
            )

            # Create result
            result = TranscriptionResult(
                text="Test transcription",
                language="en",
                confidence=0.95,
                duration_ms=500,
                model_used="small.en",
            )

            # Save to cache
            cache_key = stt._get_cache_key(sample_audio)
            stt._save_to_cache(cache_key, result)

            # Load from cache
            cached = stt._get_cached_result(cache_key)

            assert cached is not None
            assert cached.text == result.text
            assert cached.confidence == result.confidence
            assert cached.cache_hit == True

    def test_clear_cache(self, tmp_path):
        """Test cache clearing"""
        with patch('voice_assistant.stt.whisper_client.ModelManager'):
            cache_dir = tmp_path / "cache"
            cache_dir.mkdir()

            # Create some cache files
            (cache_dir / "cache1.json").write_text("{}")
            (cache_dir / "cache2.json").write_text("{}")
            (cache_dir / "other.txt").write_text("test")

            stt = WhisperSTT(
                whisper_cpp_path=tmp_path / "whisper",
                enable_cache=True,
                cache_dir=cache_dir,
            )

            count = stt.clear_cache()

            assert count == 2
            assert not (cache_dir / "cache1.json").exists()
            assert (cache_dir / "other.txt").exists()  # Not deleted


class TestIntegration:
    """Integration tests (require actual whisper.cpp installation)"""

    @pytest.mark.integration
    def test_full_transcription_pipeline(self, tmp_path):
        """Test full transcription with real whisper.cpp (if available)"""
        # This test requires actual whisper.cpp installation
        # Skip if not available
        whisper_path = Path.home() / ".voice-assistant" / "whisper.cpp" / "build" / "bin" / "main"

        if not whisper_path.exists():
            pytest.skip("whisper.cpp not installed")

        # Create simple audio (silence)
        sample_rate = 16000
        duration = 1.0
        audio = np.zeros(int(sample_rate * duration), dtype=np.int16)

        audio_input = AudioInput(samples=audio, sample_rate=sample_rate)

        stt = WhisperSTT(
            whisper_cpp_path=whisper_path,
            model=WhisperModel.SMALL_EN,
            enable_cache=True,
            enable_vad=False,  # Disable VAD for silence
        )

        # This should complete without errors
        result = stt.transcribe(audio_input)

        assert isinstance(result, TranscriptionResult)
        assert result.duration_ms > 0
