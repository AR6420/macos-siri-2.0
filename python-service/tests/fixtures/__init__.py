"""
Test fixtures package.

Provides audio samples, mock data, and test utilities.
"""

from .audio_fixtures import (
    generate_silence,
    generate_tone,
    generate_white_noise,
    generate_speech_like,
    generate_wake_word_audio,
    generate_command_audio,
    save_wav,
    load_wav,
    TEST_COMMANDS,
    create_all_fixtures,
)

from .mock_data import (
    MOCK_TRANSCRIPTIONS,
    MOCK_LLM_RESPONSES,
    MOCK_LLM_TOOL_CALLS,
    MOCK_TOOL_RESULTS,
    MOCK_CONVERSATIONS,
    MOCK_CONFIGS,
    MOCK_ERRORS,
    get_mock_transcription,
    get_mock_llm_response,
    get_mock_tool_calls,
    get_mock_tool_result,
    get_mock_conversation,
    get_mock_config,
    get_mock_error,
)

__all__ = [
    # Audio fixtures
    "generate_silence",
    "generate_tone",
    "generate_white_noise",
    "generate_speech_like",
    "generate_wake_word_audio",
    "generate_command_audio",
    "save_wav",
    "load_wav",
    "TEST_COMMANDS",
    "create_all_fixtures",
    # Mock data
    "MOCK_TRANSCRIPTIONS",
    "MOCK_LLM_RESPONSES",
    "MOCK_LLM_TOOL_CALLS",
    "MOCK_TOOL_RESULTS",
    "MOCK_CONVERSATIONS",
    "MOCK_CONFIGS",
    "MOCK_ERRORS",
    "get_mock_transcription",
    "get_mock_llm_response",
    "get_mock_tool_calls",
    "get_mock_tool_result",
    "get_mock_conversation",
    "get_mock_config",
    "get_mock_error",
]
