"""
Text rewriting module with tone adjustment.

Provides functionality to rewrite text in different tones (professional, friendly, concise)
using the configured LLM provider.
"""

import asyncio
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass

from loguru import logger

from ..llm.base import LLMProvider, Message, MessageRole, CompletionResult


class ToneType(str, Enum):
    """Supported tone types for text rewriting."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"


@dataclass
class RewriteResult:
    """Result from text rewriting operation."""
    original_text: str
    rewritten_text: str
    tone: ToneType
    tokens_used: int
    processing_time_ms: int
    success: bool
    error: str | None = None


class TextRewriter:
    """
    Text rewriting engine using LLM providers.

    Rewrites selected text with different tones while maintaining
    the original meaning and key information.
    """

    # Tone-specific prompts
    TONE_PROMPTS = {
        ToneType.PROFESSIONAL: """Rewrite the following text in a professional, formal tone suitable for business communication.
Maintain the original meaning and key points. Only return the rewritten text, nothing else.

Text: {text}""",

        ToneType.FRIENDLY: """Rewrite the following text in a friendly, casual, and warm tone.
Make it conversational while maintaining the original meaning. Only return the rewritten text, nothing else.

Text: {text}""",

        ToneType.CONCISE: """Rewrite the following text to be more concise and to the point.
Remove unnecessary words while preserving all key information. Only return the rewritten text, nothing else.

Text: {text}"""
    }

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize text rewriter.

        Args:
            llm_provider: Configured LLM provider instance
            config: Inline AI configuration
        """
        self.llm_provider = llm_provider
        self.config = config
        self.default_tone = ToneType(config.get("default_tone", "professional"))
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.7)

        logger.info(f"TextRewriter initialized with provider: {llm_provider}")

    async def rewrite(
        self,
        text: str,
        tone: ToneType | None = None,
        timeout_seconds: float = 10.0
    ) -> RewriteResult:
        """
        Rewrite text with specified tone.

        Args:
            text: Original text to rewrite
            tone: Target tone (defaults to config default_tone)
            timeout_seconds: Maximum time for operation

        Returns:
            RewriteResult with rewritten text or error
        """
        import time
        start_time = time.time()

        tone = tone or self.default_tone

        logger.info(f"Rewriting text with tone: {tone.value}")
        logger.debug(f"Original text ({len(text)} chars): {text[:100]}...")

        try:
            # Get tone-specific prompt
            prompt = self.TONE_PROMPTS[tone].format(text=text)

            # Create message for LLM
            messages = [
                Message(
                    role=MessageRole.USER,
                    content=prompt
                )
            ]

            # Call LLM with timeout
            try:
                result = await asyncio.wait_for(
                    self.llm_provider.complete(
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    ),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Rewrite timeout after {timeout_seconds}s")
                return RewriteResult(
                    original_text=text,
                    rewritten_text="",
                    tone=tone,
                    tokens_used=0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error="Rewrite operation timed out"
                )

            # Extract rewritten text
            rewritten_text = result.content.strip()

            # Remove quotes if LLM added them
            if rewritten_text.startswith('"') and rewritten_text.endswith('"'):
                rewritten_text = rewritten_text[1:-1]

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Rewrite complete in {processing_time_ms}ms")
            logger.debug(f"Rewritten text ({len(rewritten_text)} chars): {rewritten_text[:100]}...")

            return RewriteResult(
                original_text=text,
                rewritten_text=rewritten_text,
                tone=tone,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                error=None
            )

        except Exception as e:
            logger.exception(f"Error during rewrite: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return RewriteResult(
                original_text=text,
                rewritten_text="",
                tone=tone,
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                success=False,
                error=str(e)
            )

    async def rewrite_professional(self, text: str) -> RewriteResult:
        """Shortcut for professional tone rewriting."""
        return await self.rewrite(text, ToneType.PROFESSIONAL)

    async def rewrite_friendly(self, text: str) -> RewriteResult:
        """Shortcut for friendly tone rewriting."""
        return await self.rewrite(text, ToneType.FRIENDLY)

    async def rewrite_concise(self, text: str) -> RewriteResult:
        """Shortcut for concise rewriting."""
        return await self.rewrite(text, ToneType.CONCISE)
