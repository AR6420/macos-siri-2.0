"""
Text formatting module for various output formats.

Provides functionality to format text in different ways:
- Summary: Condense text to key points
- Key Points: Extract important items as bullets
- List: Convert to ordered/unordered lists
- Table: Structure data as markdown tables
"""

import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from ..llm.base import LLMProvider, Message, MessageRole, CompletionResult
from .prompts import PromptBuilder
from .summarizer import TextSummarizer, SummaryResult


class FormatType(str, Enum):
    """Supported formatting types."""
    SUMMARY = "summary"
    KEY_POINTS = "key_points"
    LIST = "list"
    TABLE = "table"


@dataclass
class FormatResult:
    """Result from text formatting operation."""
    original_text: str
    formatted_text: str
    format_type: FormatType
    tokens_used: int = 0
    processing_time_ms: int = 0
    success: bool = True
    error: str | None = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextFormatter:
    """
    Text formatting engine using LLM providers.

    Converts selected text into various structured formats while
    preserving key information and maintaining readability.
    """

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize text formatter.

        Args:
            llm_provider: Configured LLM provider instance
            config: Inline AI configuration
        """
        self.llm_provider = llm_provider
        self.config = config
        self.prompt_builder = PromptBuilder()

        # Configuration for formatting
        self.formatting_config = config.get("formatting", {})
        self.summary_length = self.formatting_config.get("summary_length", 100)
        self.key_points_count = self.formatting_config.get("key_points_count", 5)
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.5)

        # Initialize summarizer (reuse existing implementation)
        self.summarizer = TextSummarizer(llm_provider, config)

        logger.info(f"TextFormatter initialized with provider: {llm_provider}")

    async def format_text(
        self,
        text: str,
        format_type: FormatType,
        timeout_seconds: float = 10.0,
        **kwargs
    ) -> FormatResult:
        """
        Format text in specified format type.

        Args:
            text: Original text to format
            format_type: Target format type
            timeout_seconds: Maximum time for operation
            **kwargs: Format-specific parameters

        Returns:
            FormatResult with formatted text
        """
        logger.info(f"Formatting text as {format_type.value} ({len(text)} chars)")

        # Route to appropriate formatter
        formatters = {
            FormatType.SUMMARY: self.summary,
            FormatType.KEY_POINTS: self.key_points,
            FormatType.LIST: self.to_list,
            FormatType.TABLE: self.to_table,
        }

        formatter = formatters.get(format_type)
        if not formatter:
            return FormatResult(
                original_text=text,
                formatted_text="",
                format_type=format_type,
                success=False,
                error=f"Unknown format type: {format_type}"
            )

        return await formatter(text, timeout_seconds=timeout_seconds, **kwargs)

    async def summary(
        self,
        text: str,
        max_sentences: int = 3,
        timeout_seconds: float = 10.0
    ) -> FormatResult:
        """
        Create a summary of the text.

        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary
            timeout_seconds: Maximum time for operation

        Returns:
            FormatResult with summary
        """
        start_time = time.time()

        logger.info(f"Creating summary ({max_sentences} sentences)")

        try:
            # Use existing summarizer
            summary_result = await self.summarizer.summarize(
                text,
                max_sentences=max_sentences,
                timeout_seconds=timeout_seconds
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            if summary_result.success:
                return FormatResult(
                    original_text=text,
                    formatted_text=summary_result.summary,
                    format_type=FormatType.SUMMARY,
                    tokens_used=summary_result.tokens_used,
                    processing_time_ms=processing_time_ms,
                    success=True,
                    metadata={
                        "compression_ratio": summary_result.compression_ratio,
                        "max_sentences": max_sentences
                    }
                )
            else:
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.SUMMARY,
                    success=False,
                    error=summary_result.error,
                    processing_time_ms=processing_time_ms
                )

        except Exception as e:
            logger.exception(f"Error during summary formatting: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return FormatResult(
                original_text=text,
                formatted_text="",
                format_type=FormatType.SUMMARY,
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    async def key_points(
        self,
        text: str,
        num_points: int | None = None,
        timeout_seconds: float = 10.0
    ) -> FormatResult:
        """
        Extract key points as a bulleted list.

        Args:
            text: Text to extract key points from
            num_points: Specific number of points (None = auto-detect 3-7)
            timeout_seconds: Maximum time for operation

        Returns:
            FormatResult with key points as markdown bullets
        """
        start_time = time.time()

        # Use configured default if not specified
        if num_points is None:
            num_points = self.key_points_count

        logger.info(f"Extracting {num_points if num_points else 'auto'} key points")
        logger.debug(f"Original text: {text[:200]}...")

        try:
            # Validate text
            is_valid, warning = self.prompt_builder.validate_text_length(
                text, min_length=10, max_length=5000
            )

            if not is_valid:
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.KEY_POINTS,
                    success=False,
                    error=warning,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            if warning:
                logger.warning(warning)

            # Build prompt
            prompt = self.prompt_builder.build_key_points_prompt(text, num_points)

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
                logger.error(f"Key points timeout after {timeout_seconds}s")
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.KEY_POINTS,
                    success=False,
                    error="Key points extraction timed out",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Extract formatted text
            formatted = result.content.strip()

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Key points extracted in {processing_time_ms}ms")
            logger.debug(f"Key points: {formatted[:200]}...")

            # Count actual bullet points
            bullet_count = formatted.count('\n- ') + formatted.count('\n* ')

            return FormatResult(
                original_text=text,
                formatted_text=formatted,
                format_type=FormatType.KEY_POINTS,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                metadata={
                    "requested_points": num_points,
                    "actual_points": bullet_count
                }
            )

        except Exception as e:
            logger.exception(f"Error during key points extraction: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return FormatResult(
                original_text=text,
                formatted_text="",
                format_type=FormatType.KEY_POINTS,
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    async def to_list(
        self,
        text: str,
        timeout_seconds: float = 10.0
    ) -> FormatResult:
        """
        Convert text to a well-organized list (numbered or bulleted).

        The LLM will choose the appropriate list type based on content:
        - Numbered for sequential/ordered items
        - Bulleted for unordered items

        Args:
            text: Text to convert to list
            timeout_seconds: Maximum time for operation

        Returns:
            FormatResult with formatted list
        """
        start_time = time.time()

        logger.info(f"Converting text to list format")
        logger.debug(f"Original text: {text[:200]}...")

        try:
            # Validate text
            is_valid, warning = self.prompt_builder.validate_text_length(
                text, min_length=10, max_length=5000
            )

            if not is_valid:
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.LIST,
                    success=False,
                    error=warning,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            if warning:
                logger.warning(warning)

            # Build prompt
            prompt = self.prompt_builder.build_list_prompt(text)

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
                logger.error(f"List formatting timeout after {timeout_seconds}s")
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.LIST,
                    success=False,
                    error="List formatting timed out",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Extract formatted text
            formatted = result.content.strip()

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Detect list type
            is_numbered = bool(
                '\n1. ' in formatted or
                '\n1) ' in formatted or
                formatted.startswith('1. ') or
                formatted.startswith('1) ')
            )
            is_bulleted = bool('\n- ' in formatted or '\n* ' in formatted)

            list_type = "numbered" if is_numbered else "bulleted" if is_bulleted else "unknown"

            logger.info(f"List formatted ({list_type}) in {processing_time_ms}ms")
            logger.debug(f"Formatted list: {formatted[:200]}...")

            return FormatResult(
                original_text=text,
                formatted_text=formatted,
                format_type=FormatType.LIST,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                metadata={
                    "list_type": list_type
                }
            )

        except Exception as e:
            logger.exception(f"Error during list formatting: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return FormatResult(
                original_text=text,
                formatted_text="",
                format_type=FormatType.LIST,
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    async def to_table(
        self,
        text: str,
        timeout_seconds: float = 10.0
    ) -> FormatResult:
        """
        Convert text to a markdown table format.

        The LLM will identify appropriate columns and rows based on
        the structure of the content.

        Args:
            text: Text to convert to table
            timeout_seconds: Maximum time for operation

        Returns:
            FormatResult with formatted markdown table
        """
        start_time = time.time()

        logger.info(f"Converting text to table format")
        logger.debug(f"Original text: {text[:200]}...")

        try:
            # Validate text
            is_valid, warning = self.prompt_builder.validate_text_length(
                text, min_length=20, max_length=5000
            )

            if not is_valid:
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.TABLE,
                    success=False,
                    error=warning,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            if warning:
                logger.warning(warning)

            # Build prompt
            prompt = self.prompt_builder.build_table_prompt(text)

            # Create message for LLM
            messages = [
                Message(
                    role=MessageRole.USER,
                    content=prompt
                )
            ]

            # Call LLM with timeout (tables may need more time)
            try:
                result = await asyncio.wait_for(
                    self.llm_provider.complete(
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens * 2  # Tables can be longer
                    ),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Table formatting timeout after {timeout_seconds}s")
                return FormatResult(
                    original_text=text,
                    formatted_text="",
                    format_type=FormatType.TABLE,
                    success=False,
                    error="Table formatting timed out",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Extract formatted text
            formatted = result.content.strip()

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Analyze table structure
            table_metadata = self._analyze_table(formatted)

            logger.info(
                f"Table formatted ({table_metadata['rows']}x{table_metadata['columns']}) "
                f"in {processing_time_ms}ms"
            )
            logger.debug(f"Formatted table: {formatted[:200]}...")

            return FormatResult(
                original_text=text,
                formatted_text=formatted,
                format_type=FormatType.TABLE,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                metadata=table_metadata
            )

        except Exception as e:
            logger.exception(f"Error during table formatting: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return FormatResult(
                original_text=text,
                formatted_text="",
                format_type=FormatType.TABLE,
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    def _analyze_table(self, table_text: str) -> Dict[str, Any]:
        """
        Analyze markdown table structure.

        Args:
            table_text: Markdown table text

        Returns:
            Dictionary with table metadata
        """
        lines = table_text.strip().split('\n')

        # Filter out empty lines
        lines = [line for line in lines if line.strip()]

        if not lines:
            return {"rows": 0, "columns": 0, "has_header": False}

        # Count columns from first row
        first_row = lines[0]
        columns = first_row.count('|') - 1 if first_row.count('|') > 0 else 0

        # Check for header separator (---|---|---)
        has_header = False
        header_row_index = -1

        for i, line in enumerate(lines):
            if '---' in line or ':-:' in line or ':--' in line or '--:' in line:
                has_header = True
                header_row_index = i
                break

        # Count data rows (excluding header and separator)
        if has_header and header_row_index >= 0:
            rows = len(lines) - 1  # Exclude separator
        else:
            rows = len(lines)

        return {
            "rows": rows,
            "columns": columns,
            "has_header": has_header
        }

    # Convenience methods
    async def summarize(self, text: str, max_sentences: int = 3) -> FormatResult:
        """Shortcut for summary formatting."""
        return await self.summary(text, max_sentences=max_sentences)

    async def extract_key_points(self, text: str, num_points: int | None = None) -> FormatResult:
        """Shortcut for key points extraction."""
        return await self.key_points(text, num_points=num_points)

    async def listify(self, text: str) -> FormatResult:
        """Shortcut for list formatting."""
        return await self.to_list(text)

    async def tablify(self, text: str) -> FormatResult:
        """Shortcut for table formatting."""
        return await self.to_table(text)


__all__ = ["TextFormatter", "FormatResult", "FormatType"]
