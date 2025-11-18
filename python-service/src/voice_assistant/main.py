"""
Main entry point for Voice Assistant backend service.

This module initializes and runs the voice assistant service, coordinating
between all subsystems (audio, STT, LLM, MCP, TTS).
"""

import sys
import asyncio
import signal
import json
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

# Import will be added as modules are implemented
# from .orchestrator import VoiceAssistant


def setup_logging(config: dict) -> None:
    """Setup logging configuration."""
    log_level = config.get("app", {}).get("log_level", "INFO")
    log_dir = Path(config.get("app", {}).get("log_dir", "/tmp/voice-assistant/logs"))

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Add file handler
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    # Add error file handler
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    logger.info(f"Logging initialized at level {log_level}")
    logger.info(f"Log directory: {log_dir}")


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_paths = [
        Path.home() / "Library/Application Support/VoiceAssistant/config.yaml",
        Path(__file__).parent.parent.parent / "config.yaml",
        Path("config.yaml"),
    ]

    for config_path in config_paths:
        if config_path.exists():
            logger.info(f"Loading configuration from: {config_path}")
            with open(config_path) as f:
                return yaml.safe_load(f)

    logger.error("No configuration file found")
    logger.info(f"Searched paths: {[str(p) for p in config_paths]}")
    raise FileNotFoundError("Configuration file not found")


async def main_async() -> None:
    """Async main function."""
    logger.info("Voice Assistant backend starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    # Load configuration
    config = load_config()
    logger.info(f"Configuration loaded: {config.get('app', {}).get('name', 'Voice Assistant')}")

    # Import orchestrator
    from .orchestrator import VoiceAssistant, AssistantStatus

    # Initialize Voice Assistant
    logger.info("Initializing Voice Assistant orchestrator...")
    assistant = VoiceAssistant(config)

    try:
        # Initialize all subsystems
        await assistant.initialize()
        logger.info("Voice Assistant initialized successfully")

        # Setup status callback for JSON protocol
        def status_callback(status: AssistantStatus):
            """Send status updates to Swift app via JSON"""
            status_msg = {
                "type": "status_update",
                "status": status.value,
                "timestamp": asyncio.get_event_loop().time()
            }
            print(f"STATUS: {json.dumps(status_msg)}", flush=True)

        assistant.set_status_callback(status_callback)

        # Start listening
        await assistant.start()
        logger.info("Voice Assistant started, listening for wake word...")

        # Keep running and handle commands from stdin (JSON protocol)
        logger.info("Service ready - awaiting commands")
        logger.info("Press Ctrl+C to stop")

        # Start stdin command handler
        asyncio.create_task(handle_stdin_commands(assistant))

        # Keep running
        while assistant._running:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        logger.info("Service shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")
    finally:
        # Cleanup
        await assistant.cleanup()
        logger.info("Voice Assistant shutdown complete")


async def handle_stdin_commands(assistant) -> None:
    """
    Handle commands from stdin (JSON protocol for Swift app communication).

    Commands:
    - {"command": "start"} - Start listening
    - {"command": "stop"} - Stop listening
    - {"command": "interrupt"} - Interrupt current processing
    - {"command": "clear_conversation"} - Clear conversation history
    - {"command": "get_status"} - Get current status
    - {"command": "get_metrics"} - Get performance metrics

    Inline AI Commands:
    - {"command": "rewrite_text", "text": "...", "tone": "professional|friendly|concise"} - Rewrite text with tone
    - {"command": "summarize_text", "text": "...", "max_sentences": 3} - Summarize text
    - {"command": "proofread_text", "text": "...", "show_changes": true} - Proofread and correct text
    - {"command": "format_text", "text": "...", "format": "summary|key_points|list|table"} - Format text
    - {"command": "compose_text", "prompt": "...", "context": "..."} - Generate new content

    Args:
        assistant: VoiceAssistant instance
    """
    import json
    import sys

    logger.info("Stdin command handler started")

    # Initialize inline AI components
    from .inline_ai import (
        TextRewriter,
        TextSummarizer,
        TextProofreader,
        TextFormatter,
        ContentComposer,
        ToneType,
        FormatType
    )
    from .llm.factory import ProviderFactory

    # Get configuration
    config = load_config()
    inline_ai_config = config.get("inline_ai", {})

    # Create LLM provider for inline AI (shared with main assistant)
    llm_provider = ProviderFactory.create_from_config(config)

    # Initialize all inline AI components
    rewriter = TextRewriter(llm_provider, inline_ai_config)
    summarizer = TextSummarizer(llm_provider, inline_ai_config)
    proofreader = TextProofreader(llm_provider, inline_ai_config)
    formatter = TextFormatter(llm_provider, inline_ai_config)
    composer = ContentComposer(llm_provider, inline_ai_config)

    logger.info("Inline AI components initialized (rewriter, summarizer, proofreader, formatter, composer)")

    loop = asyncio.get_event_loop()

    def read_stdin():
        """Read line from stdin (blocking)"""
        try:
            return sys.stdin.readline()
        except:
            return None

    while True:
        try:
            # Read from stdin in executor to avoid blocking
            line = await loop.run_in_executor(None, read_stdin)

            if not line:
                await asyncio.sleep(0.1)
                continue

            line = line.strip()
            if not line:
                continue

            # Parse JSON command
            try:
                command_data = json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON command: {line}")
                continue

            command = command_data.get("command")

            # Handle commands
            if command == "start":
                await assistant.start()
                print(json.dumps({"response": "started"}), flush=True)

            elif command == "stop":
                await assistant.stop()
                print(json.dumps({"response": "stopped"}), flush=True)

            elif command == "interrupt":
                await assistant.interrupt()
                print(json.dumps({"response": "interrupted"}), flush=True)

            elif command == "clear_conversation":
                await assistant.clear_conversation()
                print(json.dumps({"response": "conversation_cleared"}), flush=True)

            elif command == "get_status":
                status_info = {
                    "response": "status",
                    "status": assistant.get_status().value,
                    "conversation": assistant.get_conversation_info(),
                }
                print(json.dumps(status_info), flush=True)

            elif command == "get_metrics":
                metrics = assistant.get_metrics()
                print(json.dumps({"response": "metrics", "data": metrics}), flush=True)

            elif command == "rewrite_text":
                # Rewrite text with specified tone
                text = command_data.get("text", "")
                tone_str = command_data.get("tone", "professional")

                if not text:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": "No text provided for rewriting"
                    }), flush=True)
                    continue

                try:
                    # Convert tone string to ToneType
                    tone = ToneType(tone_str.lower())

                    # Perform rewrite
                    result = await rewriter.rewrite(text, tone)

                    if result.success:
                        print(json.dumps({
                            "type": "rewrite_complete",
                            "original": result.original_text,
                            "rewritten": result.rewritten_text,
                            "tone": tone.value,
                            "tokens_used": result.tokens_used,
                            "processing_time_ms": result.processing_time_ms
                        }), flush=True)
                    else:
                        print(json.dumps({
                            "type": "inline_ai_error",
                            "error": result.error or "Rewrite failed"
                        }), flush=True)

                except ValueError:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": f"Invalid tone: {tone_str}. Use professional, friendly, or concise."
                    }), flush=True)
                except Exception as e:
                    logger.exception(f"Error during rewrite: {e}")
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": str(e)
                    }), flush=True)

            elif command == "summarize_text":
                # Summarize text
                text = command_data.get("text", "")
                max_sentences = command_data.get("max_sentences", 3)

                if not text:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": "No text provided for summarization"
                    }), flush=True)
                    continue

                try:
                    # Perform summarization
                    result = await summarizer.summarize(text, max_sentences=max_sentences)

                    if result.success:
                        print(json.dumps({
                            "type": "summarize_complete",
                            "original": result.original_text,
                            "summary": result.summary,
                            "tokens_used": result.tokens_used,
                            "processing_time_ms": result.processing_time_ms,
                            "compression_ratio": result.compression_ratio
                        }), flush=True)
                    else:
                        print(json.dumps({
                            "type": "inline_ai_error",
                            "error": result.error or "Summarization failed"
                        }), flush=True)

                except Exception as e:
                    logger.exception(f"Error during summarization: {e}")
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": str(e)
                    }), flush=True)

            elif command == "proofread_text":
                # Proofread text
                text = command_data.get("text", "")
                show_changes = command_data.get("show_changes", True)

                if not text:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": "No text provided for proofreading"
                    }), flush=True)
                    continue

                try:
                    # Perform proofreading
                    result = await proofreader.proofread(text, show_changes=show_changes)

                    if result.success:
                        # Convert TextChange objects to dictionaries
                        changes_list = [
                            {
                                "type": change.type,
                                "original": change.original,
                                "corrected": change.corrected,
                                "description": change.description,
                                "position": change.position
                            }
                            for change in result.changes
                        ]

                        print(json.dumps({
                            "type": "proofread_complete",
                            "original": result.original_text,
                            "proofread": result.proofread_text,
                            "changes": changes_list,
                            "has_changes": result.has_changes,
                            "num_changes": result.num_changes,
                            "tokens_used": result.tokens_used,
                            "processing_time_ms": result.processing_time_ms
                        }), flush=True)
                    else:
                        print(json.dumps({
                            "type": "inline_ai_error",
                            "error": result.error or "Proofreading failed"
                        }), flush=True)

                except Exception as e:
                    logger.exception(f"Error during proofreading: {e}")
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": str(e)
                    }), flush=True)

            elif command == "format_text":
                # Format text in various ways
                text = command_data.get("text", "")
                format_type_str = command_data.get("format", "summary")

                if not text:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": "No text provided for formatting"
                    }), flush=True)
                    continue

                try:
                    # Convert format string to FormatType
                    format_type = FormatType(format_type_str.lower())

                    # Get format-specific parameters
                    kwargs = {}
                    if format_type == FormatType.SUMMARY:
                        kwargs["max_sentences"] = command_data.get("max_sentences", 3)
                    elif format_type == FormatType.KEY_POINTS:
                        kwargs["num_points"] = command_data.get("num_points")

                    # Perform formatting
                    result = await formatter.format_text(text, format_type, **kwargs)

                    if result.success:
                        print(json.dumps({
                            "type": "format_complete",
                            "original": result.original_text,
                            "formatted": result.formatted_text,
                            "format_type": format_type.value,
                            "tokens_used": result.tokens_used,
                            "processing_time_ms": result.processing_time_ms,
                            "metadata": result.metadata or {}
                        }), flush=True)
                    else:
                        print(json.dumps({
                            "type": "inline_ai_error",
                            "error": result.error or "Formatting failed"
                        }), flush=True)

                except ValueError:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": f"Invalid format type: {format_type_str}. Use summary, key_points, list, or table."
                    }), flush=True)
                except Exception as e:
                    logger.exception(f"Error during formatting: {e}")
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": str(e)
                    }), flush=True)

            elif command == "compose_text":
                # Compose new content from prompt
                prompt = command_data.get("prompt", "")
                context = command_data.get("context")
                max_length = command_data.get("max_length")
                temperature = command_data.get("temperature")

                if not prompt:
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": "No prompt provided for composition"
                    }), flush=True)
                    continue

                try:
                    # Perform composition
                    result = await composer.compose(
                        prompt=prompt,
                        context=context,
                        max_length=max_length,
                        temperature=temperature
                    )

                    if result.success:
                        print(json.dumps({
                            "type": "compose_complete",
                            "prompt": result.prompt,
                            "context": result.context,
                            "content": result.composed_text,
                            "word_count": result.word_count,
                            "char_count": result.char_count,
                            "tokens_used": result.tokens_used,
                            "processing_time_ms": result.processing_time_ms,
                            "metadata": result.metadata or {}
                        }), flush=True)
                    else:
                        print(json.dumps({
                            "type": "inline_ai_error",
                            "error": result.error or "Composition failed"
                        }), flush=True)

                except Exception as e:
                    logger.exception(f"Error during composition: {e}")
                    print(json.dumps({
                        "type": "inline_ai_error",
                        "error": str(e)
                    }), flush=True)

            else:
                logger.warning(f"Unknown command: {command}")
                print(json.dumps({"response": "error", "message": f"Unknown command: {command}"}), flush=True)

        except asyncio.CancelledError:
            logger.info("Command handler cancelled")
            break
        except Exception as e:
            logger.error(f"Error handling command: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main() -> None:
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load config for logging setup
        config = load_config()
        setup_logging(config)

        # Run async main
        asyncio.run(main_async())

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
