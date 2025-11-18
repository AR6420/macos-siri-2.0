"""
Basic tests to verify project structure and configuration.
"""

import pytest
from pathlib import Path
import yaml


def test_package_imports():
    """Test that the package can be imported."""
    import voice_assistant
    assert voice_assistant.__version__ == "1.0.0"
    assert voice_assistant.__license__ == "Apache-2.0"


def test_config_file_exists():
    """Test that config.yaml exists and is valid."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    assert config_path.exists(), "config.yaml not found"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert config is not None
    assert "app" in config
    assert "llm" in config
    assert "audio" in config
    assert "stt" in config


def test_config_structure():
    """Test configuration structure is correct."""
    config_path = Path(__file__).parent.parent / "config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Test app config
    assert config["app"]["version"] == "1.0.0"
    assert config["app"]["name"] == "Voice Assistant"

    # Test LLM backends defined
    assert "local_gpt_oss" in config["llm"]
    assert "openai" in config["llm"]
    assert "anthropic" in config["llm"]
    assert "openrouter" in config["llm"]

    # Test audio config
    assert "wake_word" in config["audio"]
    assert "vad" in config["audio"]

    # Test STT config
    assert "engine" in config["stt"]
    assert config["stt"]["engine"] == "whisper_cpp"


def test_project_structure():
    """Test that all required directories exist."""
    project_root = Path(__file__).parent.parent.parent

    required_dirs = [
        "python-service/src/voice_assistant",
        "python-service/src/voice_assistant/audio",
        "python-service/src/voice_assistant/stt",
        "python-service/src/voice_assistant/llm",
        "python-service/src/voice_assistant/llm/providers",
        "python-service/src/voice_assistant/mcp",
        "python-service/src/voice_assistant/mcp/tools",
        "python-service/tests",
        "scripts",
        "docs",
        "swift-app",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory not found: {dir_path}"


def test_scripts_exist():
    """Test that all required scripts exist."""
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / "scripts"

    required_scripts = [
        "setup_whisper.sh",
        "build_dmg.sh",
        "build_pkg.sh",
    ]

    for script in required_scripts:
        script_path = scripts_dir / script
        assert script_path.exists(), f"Script not found: {script}"
        assert script_path.stat().st_mode & 0o111, f"Script not executable: {script}"


def test_documentation_exists():
    """Test that documentation files exist."""
    project_root = Path(__file__).parent.parent.parent

    required_docs = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CLAUDE.md",
        "docs/SETUP.md",
        "docs/USAGE.md",
        "docs/TROUBLESHOOTING.md",
    ]

    for doc in required_docs:
        doc_path = project_root / doc
        assert doc_path.exists(), f"Documentation not found: {doc}"
