"""
Example usage of the LLM module.

Demonstrates how to use different providers and features.
"""

import asyncio
import os
from pathlib import Path
import yaml

from voice_assistant.llm import (
    ProviderFactory,
    Message,
    MessageRole,
    ToolDefinition,
    ConversationContext,
)


async def example_local_provider():
    """Example using local gpt-oss provider."""
    print("=" * 60)
    print("Example 1: Local GPT-OSS Provider")
    print("=" * 60)

    config = {
        "llm": {
            "backend": "local_gpt_oss",
            "local_gpt_oss": {
                "base_url": "http://localhost:8080",
                "model": "gpt-oss:120b",
                "timeout": 120,
                "max_tokens": 1024,
                "temperature": 0.7
            }
        }
    }

    # Create provider
    provider = ProviderFactory.create_from_config(config)
    print(f"Created provider: {provider}")

    # Create messages
    messages = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        Message(role=MessageRole.USER, content="What is 2+2?"),
    ]

    try:
        # Get completion
        result = await provider.complete(messages)
        print(f"\nResponse: {result.content}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Model: {result.model}")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure MLX server is running on localhost:8080")
    finally:
        await provider.close()


async def example_streaming():
    """Example using streaming completion."""
    print("\n" + "=" * 60)
    print("Example 2: Streaming Responses")
    print("=" * 60)

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

    provider = ProviderFactory.create_from_config(config)

    messages = [
        Message(role=MessageRole.USER, content="Count from 1 to 5 slowly."),
    ]

    try:
        print("\nStreaming response: ", end="", flush=True)
        async for chunk in provider.stream_complete(messages):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await provider.close()


async def example_tool_calling():
    """Example with tool calling."""
    print("\n" + "=" * 60)
    print("Example 3: Tool Calling")
    print("=" * 60)

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

    provider = ProviderFactory.create_from_config(config)

    # Define a calculator tool
    calculator_tool = ToolDefinition(
        name="calculator",
        description="Perform mathematical calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    )

    messages = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful math assistant."),
        Message(role=MessageRole.USER, content="What is 25 * 4?"),
    ]

    try:
        result = await provider.complete(messages, tools=[calculator_tool])

        if result.has_tool_calls:
            print("\nLLM wants to call tools:")
            for tool_call in result.tool_calls:
                print(f"  - {tool_call.name}({tool_call.arguments})")

            # Simulate executing the tool
            tool_result = "100"

            # Add tool result to messages
            messages.append(Message(
                role=MessageRole.ASSISTANT,
                content=""
            ))
            messages.append(Message(
                role=MessageRole.TOOL,
                content=tool_result,
                tool_call_id=result.tool_calls[0].id,
                name="calculator"
            ))

            # Get final response
            final_result = await provider.complete(messages, tools=[calculator_tool])
            print(f"\nFinal response: {final_result.content}")
        else:
            print(f"\nDirect response: {result.content}")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await provider.close()


async def example_conversation_context():
    """Example using conversation context."""
    print("\n" + "=" * 60)
    print("Example 4: Conversation Context Management")
    print("=" * 60)

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

    provider = ProviderFactory.create_from_config(config)

    # Create conversation context
    context = ConversationContext(
        max_turns=5,
        system_message="You are a helpful assistant. Keep responses brief."
    )

    print(f"Created context: {context}")

    # Simulate multi-turn conversation
    turns = [
        "My name is Alice.",
        "What is my name?",
        "What is 10 + 5?",
        "What is that number times 2?",
    ]

    try:
        for user_input in turns:
            print(f"\nUser: {user_input}")

            # Add user message
            context.add_user_message(user_input)

            # Get completion
            result = await provider.complete(context.get_messages())

            # Add assistant response
            context.add_assistant_message(result.content)

            print(f"Assistant: {result.content}")
            print(f"Context: {context}")

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await provider.close()


async def example_multiple_providers():
    """Example switching between providers."""
    print("\n" + "=" * 60)
    print("Example 5: Multiple Providers")
    print("=" * 60)

    # Try different providers
    providers_config = [
        ("local_gpt_oss", {
            "llm": {
                "backend": "local_gpt_oss",
                "local_gpt_oss": {
                    "base_url": "http://localhost:8080",
                    "model": "gpt-oss:120b"
                }
            }
        }),
        # Uncomment if you have API keys set
        # ("openai", {
        #     "llm": {
        #         "backend": "openai",
        #         "openai": {
        #             "model": "gpt-4o",
        #             "api_key_env": "OPENAI_API_KEY"
        #         }
        #     }
        # }),
    ]

    message = [Message(role=MessageRole.USER, content="Say hello!")]

    for name, config in providers_config:
        try:
            provider = ProviderFactory.create_from_config(config)
            print(f"\n{name}: ", end="")
            result = await provider.complete(message)
            print(result.content[:50])
            await provider.close()
        except Exception as e:
            print(f"Error with {name}: {e}")


async def example_load_from_config_file():
    """Example loading configuration from YAML file."""
    print("\n" + "=" * 60)
    print("Example 6: Load from Config File")
    print("=" * 60)

    config_path = Path(__file__).parent.parent / "config.yaml"

    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)

        print(f"Loaded config from: {config_path}")
        print(f"Backend: {config['llm']['backend']}")

        try:
            provider = ProviderFactory.create_from_config(config)
            print(f"Created provider: {provider}")

            messages = [
                Message(role=MessageRole.USER, content="Hello!"),
            ]

            result = await provider.complete(messages)
            print(f"Response: {result.content}")

            await provider.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Config file not found: {config_path}")


async def main():
    """Run all examples."""
    print("LLM Module Examples")
    print("=" * 60)

    # Run examples
    await example_local_provider()
    # await example_streaming()
    # await example_tool_calling()
    # await example_conversation_context()
    # await example_multiple_providers()
    # await example_load_from_config_file()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
