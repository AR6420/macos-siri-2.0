"""
Main entry point for Voice Assistant backend service.

This module initializes and runs the voice assistant service, coordinating
between all subsystems (audio, STT, LLM, MCP, TTS).
"""

import sys
import asyncio
import signal
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

    # Initialize subsystems (to be implemented by other agents)
    logger.info("Initializing subsystems...")

    # TODO: Initialize VoiceAssistant orchestrator
    # assistant = VoiceAssistant(config)
    # await assistant.start()

    logger.warning("Voice Assistant subsystems not yet implemented")
    logger.info("Run by individual agents to implement functionality")
    logger.info("See CLAUDE.md for agent responsibilities")

    # Keep running
    logger.info("Service ready (placeholder mode)")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Service shutting down...")


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
