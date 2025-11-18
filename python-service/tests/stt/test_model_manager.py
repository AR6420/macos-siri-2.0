"""
Tests for Model Manager
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from voice_assistant.stt.model_manager import ModelManager, WhisperModel


@pytest.fixture
def model_manager(tmp_path):
    """Create ModelManager instance with temporary paths"""
    return ModelManager(
        whisper_cpp_path=tmp_path / "whisper",
        models_dir=tmp_path / "models",
    )


class TestWhisperModel:
    """Test WhisperModel enum"""

    def test_model_sizes(self):
        """Test model size properties"""
        assert WhisperModel.TINY_EN.size_mb == 75
        assert WhisperModel.SMALL_EN.size_mb == 466
        assert WhisperModel.LARGE.size_mb == 2900

    def test_model_descriptions(self):
        """Test model descriptions"""
        assert "English only" in WhisperModel.SMALL_EN.description
        assert "multilingual" in WhisperModel.SMALL.description


class TestModelManager:
    """Test ModelManager"""

    def test_initialization(self, tmp_path):
        """Test ModelManager initialization"""
        manager = ModelManager(
            whisper_cpp_path=tmp_path / "whisper",
            models_dir=tmp_path / "models",
        )

        assert manager.whisper_cpp_path == tmp_path / "whisper"
        assert manager.models_dir == tmp_path / "models"
        assert manager.models_dir.exists()
        assert manager.coreml_dir.exists()

    def test_default_paths(self):
        """Test default path initialization"""
        manager = ModelManager()

        assert "whisper.cpp" in str(manager.whisper_cpp_path)
        assert ".voice-assistant" in str(manager.models_dir)

    def test_get_model_path(self, model_manager):
        """Test model path generation"""
        path = model_manager.get_model_path(WhisperModel.SMALL_EN)

        assert "ggml-small.en.bin" in str(path)
        assert str(model_manager.models_dir) in str(path)

    def test_get_coreml_path(self, model_manager):
        """Test Core ML path generation"""
        path = model_manager.get_coreml_path(WhisperModel.SMALL_EN)

        assert "ggml-small.en-encoder.mlmodelc" in str(path)
        assert str(model_manager.coreml_dir) in str(path)

    def test_has_model(self, model_manager):
        """Test model existence check"""
        assert not model_manager.has_model(WhisperModel.SMALL_EN)

        # Create model file
        model_path = model_manager.get_model_path(WhisperModel.SMALL_EN)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        assert model_manager.has_model(WhisperModel.SMALL_EN)

    def test_has_coreml_model(self, model_manager):
        """Test Core ML model existence check"""
        assert not model_manager.has_coreml_model(WhisperModel.SMALL_EN)

        # Create Core ML model directory
        coreml_path = model_manager.get_coreml_path(WhisperModel.SMALL_EN)
        coreml_path.mkdir(parents=True, exist_ok=True)

        assert model_manager.has_coreml_model(WhisperModel.SMALL_EN)

    @patch('voice_assistant.stt.model_manager.urllib.request.urlretrieve')
    def test_download_model(self, mock_urlretrieve, model_manager):
        """Test model download"""
        model_path = model_manager.get_model_path(WhisperModel.SMALL_EN)

        # Mock download
        def create_file(url, path, reporthook=None):
            Path(path).touch()

        mock_urlretrieve.side_effect = create_file

        result = model_manager.download_model(WhisperModel.SMALL_EN)

        assert result == model_path
        assert model_path.exists()
        mock_urlretrieve.assert_called_once()

    def test_download_existing_model(self, model_manager):
        """Test downloading existing model (should skip)"""
        model_path = model_manager.get_model_path(WhisperModel.SMALL_EN)
        model_path.touch()

        with patch('voice_assistant.stt.model_manager.urllib.request.urlretrieve') as mock:
            result = model_manager.download_model(WhisperModel.SMALL_EN)

            assert result == model_path
            mock.assert_not_called()

    def test_list_available_models(self, model_manager):
        """Test listing available models"""
        # Create some models
        model_manager.get_model_path(WhisperModel.SMALL_EN).touch()
        model_manager.get_coreml_path(WhisperModel.SMALL_EN).mkdir(parents=True)

        models = model_manager.list_available_models()

        assert len(models) == len(WhisperModel)

        # Find small.en in list
        small_en = next(m for m in models if m[0] == WhisperModel.SMALL_EN)
        assert small_en[1] == True  # has_base
        assert small_en[2] == True  # has_coreml

    def test_get_model_info(self, model_manager):
        """Test getting model information"""
        info = model_manager.get_model_info(WhisperModel.SMALL_EN)

        assert info['name'] == 'small.en'
        assert info['size_mb'] == 466
        assert info['downloaded'] == False
        assert info['has_coreml'] == False

        # Create model
        model_path = model_manager.get_model_path(WhisperModel.SMALL_EN)
        model_path.write_text("test" * 1000)

        info = model_manager.get_model_info(WhisperModel.SMALL_EN)
        assert info['downloaded'] == True
        assert 'file_size_mb' in info

    @patch('voice_assistant.stt.model_manager.subprocess.run')
    def test_verify_whisper_cpp_installation(self, mock_run, model_manager):
        """Test whisper.cpp installation verification"""
        # Create whisper executable
        model_manager.whisper_cpp_path.parent.mkdir(parents=True, exist_ok=True)
        model_manager.whisper_cpp_path.touch()

        mock_run.return_value = Mock(returncode=0)

        assert model_manager.verify_whisper_cpp_installation() == True
        mock_run.assert_called_once()

    def test_verify_missing_whisper_cpp(self, model_manager):
        """Test verification with missing whisper.cpp"""
        assert model_manager.verify_whisper_cpp_installation() == False

    @patch.object(ModelManager, 'download_model')
    @patch.object(ModelManager, 'convert_to_coreml')
    def test_setup_recommended_model(self, mock_convert, mock_download, model_manager, tmp_path):
        """Test recommended model setup"""
        model_path = tmp_path / "models" / "ggml-small.en.bin"
        mock_download.return_value = model_path

        result = model_manager.setup_recommended_model()

        assert result == model_path
        mock_download.assert_called_once_with(WhisperModel.SMALL_EN)
        mock_convert.assert_called_once()


class TestCoreMLConversion:
    """Test Core ML conversion (requires actual tools)"""

    @pytest.mark.integration
    def test_convert_to_coreml(self, tmp_path):
        """Test Core ML conversion (integration test)"""
        # This requires actual whisper.cpp installation
        whisper_path = Path.home() / ".voice-assistant" / "whisper.cpp" / "build" / "bin" / "main"

        if not whisper_path.exists():
            pytest.skip("whisper.cpp not installed")

        manager = ModelManager(whisper_cpp_path=whisper_path)

        # Ensure model exists
        if not manager.has_model(WhisperModel.SMALL_EN):
            pytest.skip("small.en model not downloaded")

        # Try conversion
        result = manager.convert_to_coreml(WhisperModel.SMALL_EN)

        # May fail if tools not installed, but should not crash
        if result is not None:
            assert result.exists()
