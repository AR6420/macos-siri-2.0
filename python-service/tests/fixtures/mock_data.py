"""
Mock data fixtures for testing.

Provides realistic mock responses for LLM, tools, and other components.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


# Mock STT Transcription Results
MOCK_TRANSCRIPTIONS = {
    "weather_query": {
        "text": "What is the weather like today?",
        "language": "en",
        "confidence": 0.95,
        "duration_ms": 450,
    },
    "open_safari": {
        "text": "Open Safari",
        "language": "en",
        "confidence": 0.98,
        "duration_ms": 350,
    },
    "send_message": {
        "text": "Send a message to John saying I'll be there in 10 minutes",
        "language": "en",
        "confidence": 0.92,
        "duration_ms": 600,
    },
    "time_query": {
        "text": "What time is it?",
        "language": "en",
        "confidence": 0.97,
        "duration_ms": 380,
    },
    "file_operation": {
        "text": "Create a new file called notes.txt with the content hello world",
        "language": "en",
        "confidence": 0.93,
        "duration_ms": 520,
    },
    "web_search": {
        "text": "Search the web for machine learning tutorials",
        "language": "en",
        "confidence": 0.94,
        "duration_ms": 480,
    },
    "low_confidence": {
        "text": "mumble mumble unclear",
        "language": "en",
        "confidence": 0.45,
        "duration_ms": 400,
    },
}


# Mock LLM Responses (without tool calls)
MOCK_LLM_RESPONSES = {
    "weather": {
        "content": "Based on current data, it's sunny and 72°F (22°C) today with clear skies.",
        "model": "gpt-oss:120b",
        "tokens_used": 45,
        "finish_reason": "stop",
    },
    "time": {
        "content": "It's currently 3:45 PM.",
        "model": "gpt-oss:120b",
        "tokens_used": 25,
        "finish_reason": "stop",
    },
    "joke": {
        "content": "Why did the Python programmer quit his job? Because he didn't get arrays!",
        "model": "gpt-oss:120b",
        "tokens_used": 60,
        "finish_reason": "stop",
    },
    "general_info": {
        "content": "I'd be happy to help you with that. Let me search for the information you need.",
        "model": "gpt-oss:120b",
        "tokens_used": 35,
        "finish_reason": "stop",
    },
}


# Mock LLM Responses with Tool Calls
MOCK_LLM_TOOL_CALLS = {
    "open_safari": {
        "first_response": {
            "content": "",
            "model": "gpt-oss:120b",
            "tokens_used": 30,
            "finish_reason": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_001",
                    "name": "execute_applescript",
                    "arguments": {
                        "script": 'tell application "Safari" to activate'
                    }
                }
            ],
        },
        "final_response": {
            "content": "I've opened Safari for you.",
            "model": "gpt-oss:120b",
            "tokens_used": 20,
            "finish_reason": "stop",
        },
    },
    "send_message": {
        "first_response": {
            "content": "",
            "model": "gpt-oss:120b",
            "tokens_used": 40,
            "finish_reason": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_002",
                    "name": "send_message",
                    "arguments": {
                        "recipient": "John",
                        "message": "I'll be there in 10 minutes",
                        "platform": "imessage"
                    }
                }
            ],
        },
        "final_response": {
            "content": "I've sent the message to John.",
            "model": "gpt-oss:120b",
            "tokens_used": 22,
            "finish_reason": "stop",
        },
    },
    "file_create": {
        "first_response": {
            "content": "",
            "model": "gpt-oss:120b",
            "tokens_used": 35,
            "finish_reason": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_003",
                    "name": "file_operation",
                    "arguments": {
                        "operation": "write",
                        "path": "~/notes.txt",
                        "content": "hello world"
                    }
                }
            ],
        },
        "final_response": {
            "content": "I've created the file notes.txt with your content.",
            "model": "gpt-oss:120b",
            "tokens_used": 25,
            "finish_reason": "stop",
        },
    },
    "web_search": {
        "first_response": {
            "content": "",
            "model": "gpt-oss:120b",
            "tokens_used": 30,
            "finish_reason": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_004",
                    "name": "web_search",
                    "arguments": {
                        "query": "machine learning tutorials",
                        "num_results": 5
                    }
                }
            ],
        },
        "final_response": {
            "content": "I found several great machine learning tutorials. Here are the top results:\n\n1. Fast.ai - Practical Deep Learning\n2. Coursera - Machine Learning by Andrew Ng\n3. Google's Machine Learning Crash Course\n4. Kaggle Learn - Free ML tutorials\n5. MIT OpenCourseWare - Introduction to Machine Learning",
            "model": "gpt-oss:120b",
            "tokens_used": 85,
            "finish_reason": "stop",
        },
    },
    "multi_tool": {
        "first_response": {
            "content": "",
            "model": "gpt-oss:120b",
            "tokens_used": 50,
            "finish_reason": "tool_calls",
            "tool_calls": [
                {
                    "id": "call_005",
                    "name": "get_system_info",
                    "arguments": {
                        "info_type": "battery"
                    }
                },
                {
                    "id": "call_006",
                    "name": "get_system_info",
                    "arguments": {
                        "info_type": "disk_space"
                    }
                }
            ],
        },
        "final_response": {
            "content": "Your Mac has 87% battery remaining and 245 GB of free disk space.",
            "model": "gpt-oss:120b",
            "tokens_used": 30,
            "finish_reason": "stop",
        },
    },
}


# Mock Tool Execution Results
MOCK_TOOL_RESULTS = {
    "execute_applescript_safari": {
        "success": True,
        "result": "Safari activated successfully",
        "execution_time_ms": 450,
    },
    "execute_applescript_error": {
        "success": False,
        "error": "Application 'NonExistentApp' is not running",
        "execution_time_ms": 200,
    },
    "send_message_success": {
        "success": True,
        "result": "Message sent to John via iMessage",
        "execution_time_ms": 800,
    },
    "send_message_error": {
        "success": False,
        "error": "Recipient not found",
        "execution_time_ms": 300,
    },
    "file_write_success": {
        "success": True,
        "result": "File created: ~/notes.txt",
        "execution_time_ms": 150,
    },
    "file_write_error": {
        "success": False,
        "error": "Permission denied: /System/notes.txt",
        "execution_time_ms": 100,
    },
    "web_search_success": {
        "success": True,
        "result": """1. Fast.ai - Practical Deep Learning for Coders
2. Coursera - Machine Learning Specialization
3. Google's Machine Learning Crash Course
4. Kaggle - Free Machine Learning Tutorials
5. MIT OpenCourseWare - Intro to ML""",
        "execution_time_ms": 1200,
    },
    "get_battery": {
        "success": True,
        "result": "Battery: 87%, Charging: No, Time remaining: 4h 23m",
        "execution_time_ms": 50,
    },
    "get_disk_space": {
        "success": True,
        "result": "Total: 512 GB, Used: 267 GB, Free: 245 GB (48%)",
        "execution_time_ms": 80,
    },
}


# Mock Conversation Scenarios
MOCK_CONVERSATIONS = {
    "simple_query": [
        {
            "role": "system",
            "content": "You are a helpful voice assistant for macOS.",
        },
        {
            "role": "user",
            "content": "What time is it?",
        },
        {
            "role": "assistant",
            "content": "It's currently 3:45 PM.",
        },
    ],
    "multi_turn": [
        {
            "role": "system",
            "content": "You are a helpful voice assistant for macOS.",
        },
        {
            "role": "user",
            "content": "What's the weather like?",
        },
        {
            "role": "assistant",
            "content": "It's sunny and 72°F today.",
        },
        {
            "role": "user",
            "content": "Should I bring an umbrella?",
        },
        {
            "role": "assistant",
            "content": "No, you won't need an umbrella. It's clear skies all day.",
        },
    ],
    "with_tools": [
        {
            "role": "system",
            "content": "You are a helpful voice assistant for macOS.",
        },
        {
            "role": "user",
            "content": "Open Safari",
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_001",
                    "name": "execute_applescript",
                    "arguments": {"script": 'tell application "Safari" to activate'},
                }
            ],
        },
        {
            "role": "tool",
            "content": "Safari activated successfully",
            "tool_call_id": "call_001",
        },
        {
            "role": "assistant",
            "content": "I've opened Safari for you.",
        },
    ],
    "error_recovery": [
        {
            "role": "system",
            "content": "You are a helpful voice assistant for macOS.",
        },
        {
            "role": "user",
            "content": "mumble mumble unclear",
        },
        {
            "role": "assistant",
            "content": "I'm sorry, I didn't quite catch that. Could you please repeat?",
        },
        {
            "role": "user",
            "content": "What time is it?",
        },
        {
            "role": "assistant",
            "content": "It's currently 3:45 PM.",
        },
    ],
}


# Mock Test Configurations
MOCK_CONFIGS = {
    "minimal": {
        "app": {
            "log_level": "WARNING",
        },
        "llm": {
            "backend": "local_gpt_oss",
        },
    },
    "full": {
        "app": {
            "version": "1.0.0",
            "log_level": "INFO",
            "log_dir": "/tmp/voice-assistant/logs",
        },
        "llm": {
            "backend": "local_gpt_oss",
            "local_gpt_oss": {
                "base_url": "http://localhost:8080",
                "model": "gpt-oss:120b",
                "timeout": 120,
                "max_tokens": 1024,
                "temperature": 0.7,
            },
        },
        "audio": {
            "input": {
                "sample_rate": 16000,
                "channels": 1,
            },
        },
        "stt": {
            "whisper": {
                "model": "small.en",
                "language": "en",
            },
        },
        "conversation": {
            "max_history_turns": 10,
            "max_tool_iterations": 5,
        },
    },
}


# Error Scenarios
MOCK_ERRORS = {
    "stt_timeout": {
        "type": "TimeoutError",
        "message": "STT transcription timed out after 30 seconds",
    },
    "llm_api_error": {
        "type": "APIError",
        "message": "LLM API returned 503 Service Unavailable",
    },
    "tool_execution_error": {
        "type": "ToolExecutionError",
        "message": "AppleScript execution failed: syntax error",
    },
    "permission_denied": {
        "type": "PermissionError",
        "message": "Microphone access denied",
    },
    "network_error": {
        "type": "NetworkError",
        "message": "Connection to API failed: Connection refused",
    },
}


def get_mock_transcription(scenario: str) -> Dict[str, Any]:
    """Get mock transcription result."""
    return MOCK_TRANSCRIPTIONS.get(scenario, MOCK_TRANSCRIPTIONS["weather_query"])


def get_mock_llm_response(scenario: str) -> Dict[str, Any]:
    """Get mock LLM response."""
    return MOCK_LLM_RESPONSES.get(scenario, MOCK_LLM_RESPONSES["general_info"])


def get_mock_tool_calls(scenario: str) -> Dict[str, Any]:
    """Get mock tool call responses."""
    return MOCK_LLM_TOOL_CALLS.get(scenario, MOCK_LLM_TOOL_CALLS["open_safari"])


def get_mock_tool_result(scenario: str) -> Dict[str, Any]:
    """Get mock tool execution result."""
    return MOCK_TOOL_RESULTS.get(scenario, MOCK_TOOL_RESULTS["execute_applescript_safari"])


def get_mock_conversation(scenario: str) -> List[Dict[str, Any]]:
    """Get mock conversation."""
    return MOCK_CONVERSATIONS.get(scenario, MOCK_CONVERSATIONS["simple_query"])


def get_mock_config(scenario: str) -> Dict[str, Any]:
    """Get mock configuration."""
    return MOCK_CONFIGS.get(scenario, MOCK_CONFIGS["minimal"])


def get_mock_error(scenario: str) -> Dict[str, str]:
    """Get mock error."""
    return MOCK_ERRORS.get(scenario, MOCK_ERRORS["llm_api_error"])
