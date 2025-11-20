"""
Text proofreading module with grammar, spelling, and punctuation correction.

Provides functionality to proofread and correct text using the configured LLM provider,
with optional detailed change tracking for user review.
"""

from __future__ import annotations

import asyncio
import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass, field

from loguru import logger

from ..llm.base import LLMProvider, Message, MessageRole, CompletionResult
from .prompts import PromptBuilder


@dataclass
class TextChange:
    """A single change made during proofreading."""
    type: str  # "grammar", "spelling", "punctuation", "style"
    original: str
    corrected: str
    description: str
    position: int | None = None  # Character position in original text


@dataclass
class ProofreadResult:
    """Result from text proofreading operation."""
    original_text: str
    proofread_text: str
    changes: List[TextChange] = field(default_factory=list)
    tokens_used: int = 0
    processing_time_ms: int = 0
    success: bool = True
    error: str | None = None

    @property
    def has_changes(self) -> bool:
        """Check if any changes were made."""
        return self.original_text != self.proofread_text

    @property
    def num_changes(self) -> int:
        """Get number of changes made."""
        return len(self.changes)

    def get_changes_by_type(self, change_type: str) -> List[TextChange]:
        """Get all changes of a specific type."""
        return [c for c in self.changes if c.type == change_type]


class TextProofreader:
    """
    Text proofreading engine using LLM providers.

    Corrects grammar, spelling, punctuation, and style errors while
    maintaining the original meaning and tone of the text.
    """

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize text proofreader.

        Args:
            llm_provider: Configured LLM provider instance
            config: Inline AI configuration
        """
        self.llm_provider = llm_provider
        self.config = config
        self.prompt_builder = PromptBuilder()

        # Configuration
        self.show_changes_by_default = config.get("proofread", {}).get("show_changes", True)
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.3)  # Lower for consistency

        logger.info(f"TextProofreader initialized with provider: {llm_provider}")

    async def proofread(
        self,
        text: str,
        show_changes: bool | None = None,
        timeout_seconds: float = 10.0
    ) -> ProofreadResult:
        """
        Proofread text and correct errors.

        Args:
            text: Original text to proofread
            show_changes: Whether to track detailed changes (uses config default if None)
            timeout_seconds: Maximum time for operation

        Returns:
            ProofreadResult with corrected text and optional change list
        """
        start_time = time.time()

        # Use config default if not specified
        if show_changes is None:
            show_changes = self.show_changes_by_default

        logger.info(f"Proofreading text ({len(text)} chars, show_changes={show_changes})")
        logger.debug(f"Original text: {text[:200]}...")

        try:
            # Validate text length
            is_valid, warning = self.prompt_builder.validate_text_length(
                text, min_length=1, max_length=5000
            )

            if not is_valid:
                return ProofreadResult(
                    original_text=text,
                    proofread_text="",
                    success=False,
                    error=warning,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            if warning:
                logger.warning(warning)

            # Build prompt
            prompt = self.prompt_builder.build_proofread_prompt(text, show_changes)

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
                logger.error(f"Proofread timeout after {timeout_seconds}s")
                return ProofreadResult(
                    original_text=text,
                    proofread_text="",
                    success=False,
                    error="Proofread operation timed out",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Parse result based on whether we requested changes
            if show_changes:
                proofread_text, changes = self._parse_result_with_changes(
                    result.content, text
                )
            else:
                proofread_text = self._parse_result_simple(result.content)
                changes = self._detect_changes(text, proofread_text)

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Proofread complete in {processing_time_ms}ms")
            logger.info(f"Changes made: {len(changes)}")
            logger.debug(f"Proofread text: {proofread_text[:200]}...")

            return ProofreadResult(
                original_text=text,
                proofread_text=proofread_text,
                changes=changes,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                error=None
            )

        except Exception as e:
            logger.exception(f"Error during proofreading: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return ProofreadResult(
                original_text=text,
                proofread_text="",
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    def _parse_result_simple(self, content: str) -> str:
        """
        Parse simple proofread result (just corrected text).

        Args:
            content: LLM response content

        Returns:
            Cleaned corrected text
        """
        corrected = content.strip()

        # Remove quotes if LLM added them
        if corrected.startswith('"') and corrected.endswith('"'):
            corrected = corrected[1:-1]
        elif corrected.startswith("'") and corrected.endswith("'"):
            corrected = corrected[1:-1]

        return corrected

    def _parse_result_with_changes(
        self, content: str, original: str
    ) -> tuple[str, List[TextChange]]:
        """
        Parse proofread result with detailed changes (JSON format).

        Args:
            content: LLM response content (expected to be JSON)
            original: Original text

        Returns:
            Tuple of (corrected_text, list_of_changes)
        """
        try:
            # Try to parse as JSON
            data = json.loads(content)

            corrected = data.get("corrected", "")
            change_descriptions = data.get("changes", [])

            # Convert change descriptions to TextChange objects
            changes = []
            for desc in change_descriptions:
                # Parse change description to extract type and details
                change = self._parse_change_description(desc, original, corrected)
                if change:
                    changes.append(change)

            return corrected, changes

        except json.JSONDecodeError:
            # Fallback: LLM didn't return JSON, try to extract text
            logger.warning("LLM didn't return JSON format, falling back to simple parse")
            corrected = self._parse_result_simple(content)
            changes = self._detect_changes(original, corrected)
            return corrected, changes

    def _parse_change_description(
        self, description: str, original: str, corrected: str
    ) -> TextChange | None:
        """
        Parse a change description into a TextChange object.

        Args:
            description: Description of the change
            original: Original text
            corrected: Corrected text

        Returns:
            TextChange object or None if parsing failed
        """
        # Try to determine change type from description keywords
        description_lower = description.lower()

        if any(word in description_lower for word in ["spell", "typo", "misspell"]):
            change_type = "spelling"
        elif any(word in description_lower for word in ["grammar", "tense", "subject", "verb"]):
            change_type = "grammar"
        elif any(word in description_lower for word in ["punctuation", "comma", "period", "quote"]):
            change_type = "punctuation"
        elif any(word in description_lower for word in ["style", "clarity", "word choice"]):
            change_type = "style"
        else:
            change_type = "other"

        # For now, we can't easily extract the exact original/corrected snippets
        # This would require more sophisticated NLP or asking the LLM to structure
        # the response differently. We'll use the description as-is.
        return TextChange(
            type=change_type,
            original="",
            corrected="",
            description=description,
            position=None
        )

    def _detect_changes(self, original: str, corrected: str) -> List[TextChange]:
        """
        Detect changes between original and corrected text using simple diff.

        This is a fallback when LLM doesn't provide detailed change list.

        Args:
            original: Original text
            corrected: Corrected text

        Returns:
            List of detected changes (may be simplified)
        """
        if original == corrected:
            return []

        # Simple word-level diff
        original_words = original.split()
        corrected_words = corrected.split()

        changes = []

        # Basic change detection
        if len(original_words) != len(corrected_words):
            changes.append(TextChange(
                type="structure",
                original=f"{len(original_words)} words",
                corrected=f"{len(corrected_words)} words",
                description=f"Text length changed from {len(original_words)} to {len(corrected_words)} words"
            ))

        # Check for obvious spelling/grammar changes
        # (This is simplified - a real diff would be more sophisticated)
        if original.lower() != corrected.lower():
            changes.append(TextChange(
                type="grammar",
                original="",
                corrected="",
                description="Grammar, spelling, or punctuation corrections applied"
            ))

        return changes

    async def proofread_quick(self, text: str) -> ProofreadResult:
        """
        Quick proofread without detailed change tracking.

        Args:
            text: Text to proofread

        Returns:
            ProofreadResult with corrected text
        """
        return await self.proofread(text, show_changes=False, timeout_seconds=5.0)

    async def proofread_detailed(self, text: str) -> ProofreadResult:
        """
        Detailed proofread with change tracking.

        Args:
            text: Text to proofread

        Returns:
            ProofreadResult with corrected text and detailed changes
        """
        return await self.proofread(text, show_changes=True, timeout_seconds=10.0)

    def format_changes_report(self, result: ProofreadResult) -> str:
        """
        Format a human-readable report of changes made.

        Args:
            result: ProofreadResult to format

        Returns:
            Formatted string report
        """
        if not result.success:
            return f"Proofreading failed: {result.error}"

        if not result.has_changes:
            return "No changes needed - text is already correct!"

        report = f"Proofread Report ({result.num_changes} change{'s' if result.num_changes != 1 else ''}):\n\n"

        # Group changes by type
        by_type = {}
        for change in result.changes:
            if change.type not in by_type:
                by_type[change.type] = []
            by_type[change.type].append(change)

        # Format each group
        for change_type, changes in by_type.items():
            report += f"{change_type.title()} ({len(changes)}):\n"
            for change in changes:
                report += f"  - {change.description}\n"
            report += "\n"

        report += f"\nProcessing time: {result.processing_time_ms}ms\n"
        report += f"Tokens used: {result.tokens_used}\n"

        return report


__all__ = ["TextProofreader", "ProofreadResult", "TextChange"]
