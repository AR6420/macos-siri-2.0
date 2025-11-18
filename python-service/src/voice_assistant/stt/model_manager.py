"""
Model Manager

Handles Whisper model download, caching, and management.
"""

import logging
import subprocess
import urllib.request
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperModel(Enum):
    """Available Whisper models"""

    TINY_EN = "tiny.en"
    BASE_EN = "base.en"
    SMALL_EN = "small.en"
    MEDIUM_EN = "medium.en"
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

    @property
    def size_mb(self) -> int:
        """Approximate model size in MB"""
        sizes = {
            "tiny.en": 75,
            "tiny": 75,
            "base.en": 142,
            "base": 142,
            "small.en": 466,
            "small": 466,
            "medium.en": 1500,
            "medium": 1500,
            "large": 2900,
        }
        return sizes.get(self.value, 0)

    @property
    def description(self) -> str:
        """Model description"""
        descriptions = {
            "tiny.en": "Fastest, least accurate (English only)",
            "base.en": "Fast, good for simple commands (English only)",
            "small.en": "Recommended: balanced speed/accuracy (English only)",
            "medium.en": "More accurate, slower (English only)",
            "tiny": "Fastest, least accurate (multilingual)",
            "base": "Fast (multilingual)",
            "small": "Balanced (multilingual)",
            "medium": "More accurate (multilingual)",
            "large": "Most accurate, slowest (multilingual)",
        }
        return descriptions.get(self.value, "")


class ModelManager:
    """
    Manages Whisper model downloads and paths

    Handles:
    - Model download from official sources
    - Core ML model conversion
    - Model caching and verification
    - whisper.cpp installation
    """

    BASE_MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

    def __init__(
        self,
        whisper_cpp_path: Optional[Path] = None,
        models_dir: Optional[Path] = None,
    ):
        """
        Initialize model manager

        Args:
            whisper_cpp_path: Path to whisper.cpp executable
            models_dir: Directory for storing models
        """
        # Setup paths
        if whisper_cpp_path is None:
            whisper_cpp_path = Path.home() / ".voice-assistant" / "whisper.cpp" / "build" / "bin" / "main"
        self.whisper_cpp_path = Path(whisper_cpp_path)

        if models_dir is None:
            models_dir = Path.home() / ".voice-assistant" / "models"
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Core ML models directory
        self.coreml_dir = self.models_dir / "coreml"
        self.coreml_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ModelManager initialized: models_dir={self.models_dir}")

    def get_model_path(self, model: WhisperModel) -> Path:
        """Get path to model file"""
        return self.models_dir / f"ggml-{model.value}.bin"

    def get_coreml_path(self, model: WhisperModel) -> Path:
        """Get path to Core ML model directory"""
        return self.coreml_dir / f"ggml-{model.value}-encoder.mlmodelc"

    def has_model(self, model: WhisperModel) -> bool:
        """Check if model is downloaded"""
        return self.get_model_path(model).exists()

    def has_coreml_model(self, model: WhisperModel) -> bool:
        """Check if Core ML model exists"""
        return self.get_coreml_path(model).exists()

    def download_model(self, model: WhisperModel, force: bool = False) -> Path:
        """
        Download Whisper model

        Args:
            model: Model to download
            force: Force redownload even if exists

        Returns:
            Path to downloaded model
        """
        model_path = self.get_model_path(model)

        if model_path.exists() and not force:
            logger.info(f"Model {model.value} already exists")
            return model_path

        url = f"{self.BASE_MODEL_URL}/ggml-{model.value}.bin"

        logger.info(f"Downloading {model.value} model ({model.size_mb}MB)...")
        logger.info(f"URL: {url}")

        try:
            # Download with progress
            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = downloaded / total_size * 100
                    if block_num % 100 == 0:  # Log every 100 blocks
                        logger.debug(f"Download progress: {percent:.1f}%")

            urllib.request.urlretrieve(url, model_path, reporthook=progress_hook)
            logger.info(f"Downloaded {model.value} to {model_path}")

            return model_path

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            if model_path.exists():
                model_path.unlink()  # Clean up partial download
            raise

    def convert_to_coreml(self, model: WhisperModel) -> Optional[Path]:
        """
        Convert model to Core ML format

        Args:
            model: Model to convert

        Returns:
            Path to Core ML model or None if conversion failed

        Note:
            Requires whisper.cpp to be built with Core ML support
            and ane_transformers, coremltools to be installed
        """
        if self.has_coreml_model(model):
            logger.info(f"Core ML model for {model.value} already exists")
            return self.get_coreml_path(model)

        model_path = self.get_model_path(model)
        if not model_path.exists():
            logger.error(f"Base model {model.value} not found, download first")
            return None

        logger.info(f"Converting {model.value} to Core ML format...")

        # This requires the generate-coreml-model.sh script from whisper.cpp
        whisper_cpp_dir = self.whisper_cpp_path.parent.parent.parent
        script_path = whisper_cpp_dir / "models" / "generate-coreml-model.sh"

        if not script_path.exists():
            logger.warning(
                "Core ML conversion script not found. "
                "Please run this manually in whisper.cpp directory: "
                f"./models/generate-coreml-model.sh {model.value}"
            )
            return None

        try:
            result = subprocess.run(
                [str(script_path), model.value],
                cwd=str(whisper_cpp_dir),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for conversion
            )

            if result.returncode != 0:
                logger.error(f"Core ML conversion failed: {result.stderr}")
                return None

            # Move Core ML model to our directory
            source_coreml = whisper_cpp_dir / "models" / f"ggml-{model.value}-encoder.mlmodelc"
            target_coreml = self.get_coreml_path(model)

            if source_coreml.exists():
                # Move entire directory
                import shutil
                if target_coreml.exists():
                    shutil.rmtree(target_coreml)
                shutil.move(str(source_coreml), str(target_coreml))
                logger.info(f"Core ML model converted: {target_coreml}")
                return target_coreml
            else:
                logger.error("Core ML conversion produced no output")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Core ML conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Core ML conversion failed: {e}")
            return None

    def list_available_models(self) -> list[tuple[WhisperModel, bool, bool]]:
        """
        List all available models and their status

        Returns:
            List of (model, has_base, has_coreml) tuples
        """
        models = []
        for model in WhisperModel:
            has_base = self.has_model(model)
            has_coreml = self.has_coreml_model(model)
            models.append((model, has_base, has_coreml))
        return models

    def verify_whisper_cpp_installation(self) -> bool:
        """
        Verify whisper.cpp is properly installed

        Returns:
            True if installation is valid
        """
        if not self.whisper_cpp_path.exists():
            logger.error(
                f"whisper.cpp not found at {self.whisper_cpp_path}\n"
                "Run: scripts/setup_whisper.sh"
            )
            return False

        # Try to run whisper.cpp
        try:
            result = subprocess.run(
                [str(self.whisper_cpp_path), "-h"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info("whisper.cpp installation verified")
                return True
            else:
                logger.error("whisper.cpp exists but failed to run")
                return False
        except Exception as e:
            logger.error(f"Failed to verify whisper.cpp: {e}")
            return False

    def setup_recommended_model(self) -> Path:
        """
        Download and setup the recommended model (small.en)

        Returns:
            Path to model
        """
        model = WhisperModel.SMALL_EN
        logger.info("Setting up recommended model: small.en")

        # Download base model
        model_path = self.download_model(model)

        # Try to convert to Core ML
        try:
            self.convert_to_coreml(model)
        except Exception as e:
            logger.warning(f"Core ML conversion failed, will use CPU: {e}")

        return model_path

    def get_model_info(self, model: WhisperModel) -> dict:
        """
        Get detailed information about a model

        Args:
            model: Model to query

        Returns:
            Dictionary with model information
        """
        model_path = self.get_model_path(model)
        coreml_path = self.get_coreml_path(model)

        info = {
            "name": model.value,
            "description": model.description,
            "size_mb": model.size_mb,
            "downloaded": model_path.exists(),
            "path": str(model_path) if model_path.exists() else None,
            "has_coreml": coreml_path.exists(),
            "coreml_path": str(coreml_path) if coreml_path.exists() else None,
        }

        if model_path.exists():
            info["file_size_mb"] = model_path.stat().st_size / (1024 * 1024)

        return info
