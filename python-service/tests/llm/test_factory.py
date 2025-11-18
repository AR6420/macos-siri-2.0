"""
Tests for provider factory.
"""

import os
import pytest
from voice_assistant.llm import (
    ProviderFactory,
    LocalGPTOSSProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    LLMProvider,
)


class TestProviderFactory:
    """Test ProviderFactory class."""

    def test_list_supported_backends(self):
        """Test listing supported backends."""
        backends = ProviderFactory.list_supported_backends()

        assert "local_gpt_oss" in backends
        assert "openai" in backends
        assert "anthropic" in backends
        assert "openrouter" in backends

    def test_create_local_gpt_oss(self):
        """Test creating LocalGPTOSSProvider."""
        config = {
            "llm": {
                "backend": "local_gpt_oss",
                "local_gpt_oss": {
                    "base_url": "http://localhost:8080",
                    "model": "gpt-oss:120b",
                    "timeout": 120
                }
            }
        }

        provider = ProviderFactory.create("local_gpt_oss", config)

        assert isinstance(provider, LocalGPTOSSProvider)
        assert provider.model == "gpt-oss:120b"
        assert provider.base_url == "http://localhost:8080"
        assert provider.timeout == 120

    def test_create_openai_requires_api_key(self):
        """Test that OpenAI provider requires API key."""
        config = {
            "llm": {
                "backend": "openai",
                "openai": {
                    "model": "gpt-4o",
                    "api_key_env": "OPENAI_TEST_KEY"
                }
            }
        }

        # Should raise if key not in environment
        if "OPENAI_TEST_KEY" in os.environ:
            del os.environ["OPENAI_TEST_KEY"]

        with pytest.raises(ValueError, match="API key not found"):
            ProviderFactory.create("openai", config)

    def test_create_openai_with_api_key(self):
        """Test creating OpenAI provider with API key."""
        os.environ["OPENAI_TEST_KEY"] = "test-key-123"

        config = {
            "llm": {
                "backend": "openai",
                "openai": {
                    "model": "gpt-4o",
                    "api_key_env": "OPENAI_TEST_KEY",
                    "timeout": 60
                }
            }
        }

        try:
            provider = ProviderFactory.create("openai", config)
            assert isinstance(provider, OpenAIProvider)
            assert provider.model == "gpt-4o"
        finally:
            del os.environ["OPENAI_TEST_KEY"]

    def test_create_anthropic_requires_api_key(self):
        """Test that Anthropic provider requires API key."""
        config = {
            "llm": {
                "backend": "anthropic",
                "anthropic": {
                    "model": "claude-sonnet-4-20250514",
                    "api_key_env": "ANTHROPIC_TEST_KEY"
                }
            }
        }

        # Should raise if key not in environment
        if "ANTHROPIC_TEST_KEY" in os.environ:
            del os.environ["ANTHROPIC_TEST_KEY"]

        with pytest.raises(ValueError, match="API key not found"):
            ProviderFactory.create("anthropic", config)

    def test_create_openrouter_requires_api_key(self):
        """Test that OpenRouter provider requires API key."""
        config = {
            "llm": {
                "backend": "openrouter",
                "openrouter": {
                    "model": "openai/gpt-4o",
                    "api_key_env": "OPENROUTER_TEST_KEY"
                }
            }
        }

        # Should raise if key not in environment
        if "OPENROUTER_TEST_KEY" in os.environ:
            del os.environ["OPENROUTER_TEST_KEY"]

        with pytest.raises(ValueError, match="API key not found"):
            ProviderFactory.create("openrouter", config)

    def test_create_from_config(self):
        """Test creating provider from config using create_from_config."""
        config = {
            "llm": {
                "backend": "local_gpt_oss",
                "local_gpt_oss": {
                    "base_url": "http://localhost:8080",
                    "model": "gpt-oss:120b"
                }
            }
        }

        provider = ProviderFactory.create_from_config(config)

        assert isinstance(provider, LocalGPTOSSProvider)
        assert provider.model == "gpt-oss:120b"

    def test_create_from_config_missing_llm_section(self):
        """Test that create_from_config raises on missing llm section."""
        config = {}

        with pytest.raises(ValueError, match="missing 'llm' section"):
            ProviderFactory.create_from_config(config)

    def test_create_from_config_missing_backend(self):
        """Test that create_from_config raises on missing backend."""
        config = {"llm": {}}

        with pytest.raises(ValueError, match="missing 'llm.backend'"):
            ProviderFactory.create_from_config(config)

    def test_unsupported_backend(self):
        """Test that unsupported backend raises error."""
        config = {
            "llm": {
                "backend": "unknown_backend",
                "unknown_backend": {}
            }
        }

        with pytest.raises(ValueError, match="Unsupported LLM backend"):
            ProviderFactory.create("unknown_backend", config)

    def test_missing_provider_config(self):
        """Test that missing provider config raises error."""
        config = {
            "llm": {
                "backend": "local_gpt_oss"
                # Missing local_gpt_oss section
            }
        }

        with pytest.raises(ValueError, match="missing 'llm.local_gpt_oss' section"):
            ProviderFactory.create("local_gpt_oss", config)

    def test_missing_required_fields(self):
        """Test that missing required fields raises error."""
        config = {
            "llm": {
                "backend": "local_gpt_oss",
                "local_gpt_oss": {
                    # Missing required base_url and model
                    "timeout": 120
                }
            }
        }

        with pytest.raises(ValueError, match="missing required fields"):
            ProviderFactory.create("local_gpt_oss", config)

    def test_backend_aliases(self):
        """Test that backend aliases work."""
        config = {
            "llm": {
                "backend": "openai_gpt4",
                "openai": {
                    "model": "gpt-4",
                    "api_key_env": "OPENAI_TEST_KEY"
                }
            }
        }

        os.environ["OPENAI_TEST_KEY"] = "test-key"
        try:
            provider = ProviderFactory.create("openai_gpt4", config)
            assert isinstance(provider, OpenAIProvider)
        finally:
            del os.environ["OPENAI_TEST_KEY"]

    def test_register_custom_provider(self):
        """Test registering custom provider."""

        class CustomProvider(LLMProvider):
            async def complete(self, messages, **kwargs):
                pass

            async def stream_complete(self, messages, **kwargs):
                pass

        ProviderFactory.register_provider("custom", CustomProvider)

        assert "custom" in ProviderFactory.list_supported_backends()

        config = {
            "llm": {
                "backend": "custom",
                "custom": {"model": "test"}
            }
        }

        provider = ProviderFactory.create("custom", config)
        assert isinstance(provider, CustomProvider)

    def test_register_invalid_provider(self):
        """Test that registering invalid provider raises error."""

        class NotAProvider:
            pass

        with pytest.raises(TypeError, match="must inherit from LLMProvider"):
            ProviderFactory.register_provider("invalid", NotAProvider)
