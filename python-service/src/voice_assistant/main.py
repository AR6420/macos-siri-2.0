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

    Args:
        assistant: VoiceAssistant instance
    """
    import json
    import sys

    logger.info("Stdin command handler started")

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
