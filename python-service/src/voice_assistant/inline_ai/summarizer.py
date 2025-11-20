"""
Text summarization module.

Provides functionality to summarize selected text using the configured LLM provider.
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Any
from dataclasses import dataclass

from loguru import logger

from ..llm.base import LLMProvider, Message, MessageRole, CompletionResult


@dataclass
class SummaryResult:
    """Result from text summarization operation."""
    original_text: str
    summary: str
    tokens_used: int
    processing_time_ms: int
    compression_ratio: float
    success: bool
    error: str | None = None


class TextSummarizer:
    """
    Text summarization engine using LLM providers.

    Condenses selected text into concise summaries while preserving
    key information and main points.
    """

    # Default summarization prompt
    DEFAULT_PROMPT = """Provide a concise summary of the following text in 2-3 sentences.
Capture the main points and key information. Only return the summary, nothing else.

Text: {text}"""

    # Short text summarization prompt (for very short selections)
    SHORT_PROMPT = """Provide a brief one-sentence summary of the following text.
Only return the summary, nothing else.

Text: {text}"""

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize text summarizer.

        Args:
            llm_provider: Configured LLM provider instance
            config: Inline AI configuration
        """
        self.llm_provider = llm_provider
        self.config = config
        self.max_summary_length = config.get("summary_max_length", 100)
        self.max_tokens = config.get("max_tokens", 256)
        self.temperature = config.get("temperature", 0.5)  # Lower temp for summaries

        logger.info(f"TextSummarizer initialized with provider: {llm_provider}")

    async def summarize(
        self,
        text: str,
        max_sentences: int = 3,
        timeout_seconds: float = 10.0
    ) -> SummaryResult:
        """
        Summarize text to specified number of sentences.

        Args:
            text: Original text to summarize
            max_sentences: Maximum sentences in summary
            timeout_seconds: Maximum time for operation

        Returns:
            SummaryResult with summary or error
        """
        start_time = time.time()

        logger.info(f"Summarizing text ({len(text)} chars, max {max_sentences} sentences)")
        logger.debug(f"Original text: {text[:200]}...")

        try:
            # Choose prompt based on text length
            word_count = len(text.split())

            if word_count < 50:
                # Very short text - use short prompt
                prompt = self.SHORT_PROMPT.format(text=text)
            elif max_sentences == 1:
                prompt = self.SHORT_PROMPT.format(text=text)
            else:
                # Standard summarization
                prompt = f"""Provide a concise summary of the following text in {max_sentences} sentence{'s' if max_sentences > 1 else ''}.
Capture the main points and key information. Only return the summary, nothing else.

Text: {text}"""

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
                logger.error(f"Summarization timeout after {timeout_seconds}s")
                return SummaryResult(
                    original_text=text,
                    summary="",
                    tokens_used=0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    compression_ratio=0.0,
                    success=False,
                    error="Summarization timed out"
                )

            # Extract summary
            summary = result.content.strip()

            # Remove quotes if LLM added them
            if summary.startswith('"') and summary.endswith('"'):
                summary = summary[1:-1]

            # Calculate compression ratio
            compression_ratio = len(summary) / len(text) if len(text) > 0 else 0.0

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Summarization complete in {processing_time_ms}ms")
            logger.info(f"Compression: {len(text)} -> {len(summary)} chars ({compression_ratio:.2%})")
            logger.debug(f"Summary: {summary[:100]}...")

            return SummaryResult(
                original_text=text,
                summary=summary,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                compression_ratio=compression_ratio,
                success=True,
                error=None
            )

        except Exception as e:
            logger.exception(f"Error during summarization: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return SummaryResult(
                original_text=text,
                summary="",
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                compression_ratio=0.0,
                success=False,
                error=str(e)
            )

    async def summarize_brief(self, text: str) -> SummaryResult:
        """Create a brief one-sentence summary."""
        return await self.summarize(text, max_sentences=1)

    async def summarize_detailed(self, text: str) -> SummaryResult:
        """Create a detailed 5-sentence summary."""
        return await self.summarize(text, max_sentences=5)
