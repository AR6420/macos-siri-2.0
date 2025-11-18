"""
Factory for creating LLM provider instances.

Provides a centralized way to instantiate the correct provider
based on configuration.
"""

from typing import Dict, Any
from .base import LLMProvider
from .providers import (
    LocalGPTOSSProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
)


class ProviderFactory:
    """
    Factory for creating LLM provider instances.

    Supports dynamic provider selection based on configuration.
    """

    # Registry of available providers
    _PROVIDERS = {
        "local_gpt_oss": LocalGPTOSSProvider,
        "openai": OpenAIProvider,
        "openai_gpt4": OpenAIProvider,  # Alias
        "anthropic": AnthropicProvider,
        "anthropic_claude": AnthropicProvider,  # Alias
        "openrouter": OpenRouterProvider,
    }

    @staticmethod
    def create(backend: str, config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            backend: Provider backend name (e.g., "local_gpt_oss", "openai")
            config: Full configuration dictionary with provider-specific settings

        Returns:
            Initialized LLM provider instance

        Raises:
            ValueError: If backend is not supported or configuration is invalid

        Example:
            >>> config = {
            ...     "llm": {
            ...         "backend": "local_gpt_oss",
            ...         "local_gpt_oss": {
            ...             "base_url": "http://localhost:8080",
            ...             "model": "gpt-oss:120b",
            ...             "timeout": 120
            ...         }
            ...     }
            ... }
            >>> provider = ProviderFactory.create("local_gpt_oss", config)
        """
        # Normalize backend name
        backend = backend.lower().strip()

        # Check if backend is supported
        if backend not in ProviderFactory._PROVIDERS:
            supported = ", ".join(ProviderFactory._PROVIDERS.keys())
            raise ValueError(
                f"Unsupported LLM backend: '{backend}'. "
                f"Supported backends: {supported}"
            )

        # Get provider class
        provider_class = ProviderFactory._PROVIDERS[backend]

        # Extract provider-specific config
        provider_config = ProviderFactory._get_provider_config(backend, config)

        # Validate required configuration
        ProviderFactory._validate_config(backend, provider_config)

        # Create and return provider instance
        try:
            return provider_class(provider_config)
        except Exception as e:
            raise ValueError(
                f"Failed to create {backend} provider: {e}"
            ) from e

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> LLMProvider:
        """
        Create provider directly from configuration dictionary.

        Automatically extracts backend name from config.

        Args:
            config: Configuration dictionary with 'llm.backend' key

        Returns:
            Initialized LLM provider instance

        Raises:
            ValueError: If configuration is invalid

        Example:
            >>> config = {
            ...     "llm": {
            ...         "backend": "openai",
            ...         "openai": {"model": "gpt-4o", "api_key_env": "OPENAI_API_KEY"}
            ...     }
            ... }
            >>> provider = ProviderFactory.create_from_config(config)
        """
        if "llm" not in config:
            raise ValueError("Configuration missing 'llm' section")

        llm_config = config["llm"]

        if "backend" not in llm_config:
            raise ValueError("Configuration missing 'llm.backend' key")

        backend = llm_config["backend"]
        return ProviderFactory.create(backend, config)

    @staticmethod
    def _get_provider_config(backend: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract provider-specific configuration.

        Args:
            backend: Provider backend name
            config: Full configuration dictionary

        Returns:
            Provider-specific configuration

        Raises:
            ValueError: If configuration is missing
        """
        # Handle aliases
        backend_key = backend
        if backend in ["openai_gpt4"]:
            backend_key = "openai"
        elif backend in ["anthropic_claude"]:
            backend_key = "anthropic"

        # Get LLM config section
        llm_config = config.get("llm", {})

        # Get provider-specific config
        provider_config = llm_config.get(backend_key, {})

        if not provider_config:
            raise ValueError(
                f"Configuration missing 'llm.{backend_key}' section for {backend} provider"
            )

        return provider_config

    @staticmethod
    def _validate_config(backend: str, provider_config: Dict[str, Any]):
        """
        Validate provider configuration has required fields.

        Args:
            backend: Provider backend name
            provider_config: Provider-specific configuration

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {
            "local_gpt_oss": ["base_url", "model"],
            "openai": ["model"],
            "openai_gpt4": ["model"],
            "anthropic": ["model"],
            "anthropic_claude": ["model"],
            "openrouter": ["model"],
        }

        required = required_fields.get(backend, [])

        missing = [field for field in required if field not in provider_config]

        if missing:
            raise ValueError(
                f"Configuration for {backend} missing required fields: {', '.join(missing)}"
            )

    @staticmethod
    def list_supported_backends() -> list[str]:
        """
        Get list of supported backend names.

        Returns:
            List of supported backend names
        """
        return list(ProviderFactory._PROVIDERS.keys())

    @staticmethod
    def register_provider(name: str, provider_class: type):
        """
        Register a custom provider.

        Allows extending the factory with custom provider implementations.

        Args:
            name: Backend name for the provider
            provider_class: Provider class (must inherit from LLMProvider)

        Raises:
            TypeError: If provider_class doesn't inherit from LLMProvider
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(
                f"Provider class must inherit from LLMProvider, got {provider_class}"
            )

        ProviderFactory._PROVIDERS[name.lower()] = provider_class
