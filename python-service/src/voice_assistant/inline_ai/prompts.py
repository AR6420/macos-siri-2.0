"""
Centralized prompt templates for all inline AI operations.

This module provides consistent, optimized prompts for various text processing
tasks (rewriting, proofreading, formatting, composing) that work well across
different LLM providers (Claude, GPT-4, local models).
"""

from typing import Dict, Any
from enum import Enum


class PromptType(str, Enum):
    """Types of inline AI prompts."""
    # Rewriting
    REWRITE_PROFESSIONAL = "rewrite_professional"
    REWRITE_FRIENDLY = "rewrite_friendly"
    REWRITE_CONCISE = "rewrite_concise"

    # Proofreading
    PROOFREAD = "proofread"
    PROOFREAD_WITH_CHANGES = "proofread_with_changes"

    # Formatting
    FORMAT_SUMMARY = "format_summary"
    FORMAT_KEY_POINTS = "format_key_points"
    FORMAT_LIST = "format_list"
    FORMAT_TABLE = "format_table"

    # Composing
    COMPOSE_WITH_CONTEXT = "compose_with_context"
    COMPOSE_WITHOUT_CONTEXT = "compose_without_context"


class PromptTemplates:
    """
    Collection of optimized prompt templates for inline AI operations.

    All prompts are designed to:
    1. Be clear and specific about the task
    2. Minimize token usage while maintaining quality
    3. Work consistently across different LLM providers
    4. Include output format instructions
    5. Handle edge cases gracefully
    """

    # ========== REWRITING PROMPTS ==========

    REWRITE_PROFESSIONAL = """Rewrite the following text in a professional, formal tone suitable for business communication.
Maintain the original meaning and key points. Only return the rewritten text, nothing else.

Text: {text}"""

    REWRITE_FRIENDLY = """Rewrite the following text in a friendly, casual, and warm tone.
Make it conversational while maintaining the original meaning. Only return the rewritten text, nothing else.

Text: {text}"""

    REWRITE_CONCISE = """Rewrite the following text to be more concise and to the point.
Remove unnecessary words while preserving all key information. Only return the rewritten text, nothing else.

Text: {text}"""

    # ========== PROOFREADING PROMPTS ==========

    PROOFREAD = """Proofread the following text and correct any grammar, spelling, punctuation, or style errors.
Maintain the original meaning and tone. Only return the corrected text, nothing else.

Text: {text}"""

    PROOFREAD_WITH_CHANGES = """Proofread the following text and correct any grammar, spelling, punctuation, or style errors.
Return a JSON object with two fields:
1. "corrected": The corrected text
2. "changes": A list of changes made (each change should be a string describing what was fixed)

Format your response as valid JSON only, no additional text.

Text: {text}"""

    # ========== FORMATTING PROMPTS ==========

    FORMAT_SUMMARY = """Provide a concise summary of the following text in {max_sentences} sentence{'s' if max_sentences != 1 else ''}.
Capture the main points and key information. Only return the summary, nothing else.

Text: {text}"""

    FORMAT_SUMMARY_SHORT = """Provide a brief one-sentence summary of the following text.
Only return the summary, nothing else.

Text: {text}"""

    FORMAT_KEY_POINTS = """Extract the {num_points} most important key points from the following text.
Format as a markdown bulleted list. Each point should be concise (one line).
Only return the bulleted list, nothing else.

Text: {text}"""

    FORMAT_KEY_POINTS_AUTO = """Extract the key points from the following text as a markdown bulleted list.
Identify 3-7 points depending on the content. Each point should be concise (one line).
Only return the bulleted list, nothing else.

Text: {text}"""

    FORMAT_LIST = """Convert the following text into a well-organized list.
Use numbered list if the content has sequential/ordered items.
Use bulleted list if the content has unordered items.
Format as markdown. Only return the list, nothing else.

Text: {text}"""

    FORMAT_TABLE = """Convert the following information into a markdown table format.
Identify appropriate columns and rows based on the content structure.
Use proper markdown table syntax with headers and alignment.
If the content doesn't naturally fit a table format, create the best possible organization.
Only return the markdown table, nothing else.

Text: {text}"""

    # ========== COMPOSING PROMPTS ==========

    COMPOSE_WITH_CONTEXT = """Based on the following prompt and context, generate well-written content.
Be concise, clear, and relevant to the request. Match the tone and style to what seems appropriate.

Prompt: {prompt}

Context:
{context}

Generate the requested content (return only the content, no preamble):"""

    COMPOSE_WITHOUT_CONTEXT = """Based on the following prompt, generate well-written content.
Be concise, clear, and relevant to the request. Match the tone and style to what seems appropriate.

Prompt: {prompt}

Generate the requested content (return only the content, no preamble):"""

    # ========== SPECIAL CASE PROMPTS ==========

    EMPTY_TEXT_ERROR = "No text provided"
    TEXT_TOO_SHORT_WARNING = "Text is very short (< 10 characters). Results may not be meaningful."
    TEXT_TOO_LONG_WARNING = "Text is very long (> {max_length} characters). Processing may take longer."


class PromptBuilder:
    """
    Helper class for building and customizing prompts.

    Provides methods to:
    - Select appropriate prompts based on context
    - Fill in template variables
    - Add custom instructions
    - Validate inputs
    """

    def __init__(self):
        self.templates = PromptTemplates()

    def build_rewrite_prompt(self, text: str, tone: str) -> str:
        """
        Build a rewriting prompt for the specified tone.

        Args:
            text: Text to rewrite
            tone: Target tone (professional, friendly, concise)

        Returns:
            Formatted prompt string
        """
        tone_map = {
            "professional": PromptTemplates.REWRITE_PROFESSIONAL,
            "friendly": PromptTemplates.REWRITE_FRIENDLY,
            "concise": PromptTemplates.REWRITE_CONCISE,
        }

        template = tone_map.get(tone.lower())
        if not template:
            raise ValueError(f"Unknown tone: {tone}")

        return template.format(text=text)

    def build_proofread_prompt(self, text: str, show_changes: bool = False) -> str:
        """
        Build a proofreading prompt.

        Args:
            text: Text to proofread
            show_changes: If True, request list of changes made

        Returns:
            Formatted prompt string
        """
        if show_changes:
            return PromptTemplates.PROOFREAD_WITH_CHANGES.format(text=text)
        else:
            return PromptTemplates.PROOFREAD.format(text=text)

    def build_summary_prompt(self, text: str, max_sentences: int = 3) -> str:
        """
        Build a summarization prompt.

        Args:
            text: Text to summarize
            max_sentences: Maximum sentences in summary

        Returns:
            Formatted prompt string
        """
        if max_sentences == 1 or len(text.split()) < 50:
            return PromptTemplates.FORMAT_SUMMARY_SHORT.format(text=text)
        else:
            return PromptTemplates.FORMAT_SUMMARY.format(
                text=text,
                max_sentences=max_sentences
            )

    def build_key_points_prompt(self, text: str, num_points: int | None = None) -> str:
        """
        Build a key points extraction prompt.

        Args:
            text: Text to extract key points from
            num_points: Specific number of points (None = auto-detect)

        Returns:
            Formatted prompt string
        """
        if num_points is None:
            return PromptTemplates.FORMAT_KEY_POINTS_AUTO.format(text=text)
        else:
            return PromptTemplates.FORMAT_KEY_POINTS.format(
                text=text,
                num_points=num_points
            )

    def build_list_prompt(self, text: str) -> str:
        """
        Build a list formatting prompt.

        Args:
            text: Text to convert to list

        Returns:
            Formatted prompt string
        """
        return PromptTemplates.FORMAT_LIST.format(text=text)

    def build_table_prompt(self, text: str) -> str:
        """
        Build a table formatting prompt.

        Args:
            text: Text to convert to table

        Returns:
            Formatted prompt string
        """
        return PromptTemplates.FORMAT_TABLE.format(text=text)

    def build_compose_prompt(self, prompt: str, context: str | None = None) -> str:
        """
        Build a content composition prompt.

        Args:
            prompt: User's content request
            context: Optional context to inform generation

        Returns:
            Formatted prompt string
        """
        if context:
            return PromptTemplates.COMPOSE_WITH_CONTEXT.format(
                prompt=prompt,
                context=context
            )
        else:
            return PromptTemplates.COMPOSE_WITHOUT_CONTEXT.format(
                prompt=prompt
            )

    def validate_text_length(
        self,
        text: str,
        min_length: int = 1,
        max_length: int = 10000
    ) -> tuple[bool, str | None]:
        """
        Validate text length for processing.

        Args:
            text: Text to validate
            min_length: Minimum acceptable length
            max_length: Maximum acceptable length

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if not text or len(text) < min_length:
            return False, PromptTemplates.EMPTY_TEXT_ERROR

        if len(text) < 10:
            return True, PromptTemplates.TEXT_TOO_SHORT_WARNING

        if len(text) > max_length:
            return True, PromptTemplates.TEXT_TOO_LONG_WARNING.format(
                max_length=max_length
            )

        return True, None


# Singleton instance for easy access
prompt_builder = PromptBuilder()


# Convenience functions for quick access
def get_prompt(prompt_type: PromptType, **kwargs) -> str:
    """
    Get a formatted prompt by type.

    Args:
        prompt_type: Type of prompt to get
        **kwargs: Template variables

    Returns:
        Formatted prompt string

    Example:
        >>> prompt = get_prompt(PromptType.REWRITE_PROFESSIONAL, text="Hello")
    """
    builder = PromptBuilder()

    type_to_method = {
        PromptType.REWRITE_PROFESSIONAL: lambda: builder.build_rewrite_prompt(
            kwargs['text'], 'professional'
        ),
        PromptType.REWRITE_FRIENDLY: lambda: builder.build_rewrite_prompt(
            kwargs['text'], 'friendly'
        ),
        PromptType.REWRITE_CONCISE: lambda: builder.build_rewrite_prompt(
            kwargs['text'], 'concise'
        ),
        PromptType.PROOFREAD: lambda: builder.build_proofread_prompt(
            kwargs['text'], show_changes=False
        ),
        PromptType.PROOFREAD_WITH_CHANGES: lambda: builder.build_proofread_prompt(
            kwargs['text'], show_changes=True
        ),
        PromptType.FORMAT_SUMMARY: lambda: builder.build_summary_prompt(
            kwargs['text'], kwargs.get('max_sentences', 3)
        ),
        PromptType.FORMAT_KEY_POINTS: lambda: builder.build_key_points_prompt(
            kwargs['text'], kwargs.get('num_points')
        ),
        PromptType.FORMAT_LIST: lambda: builder.build_list_prompt(
            kwargs['text']
        ),
        PromptType.FORMAT_TABLE: lambda: builder.build_table_prompt(
            kwargs['text']
        ),
        PromptType.COMPOSE_WITH_CONTEXT: lambda: builder.build_compose_prompt(
            kwargs['prompt'], kwargs.get('context')
        ),
        PromptType.COMPOSE_WITHOUT_CONTEXT: lambda: builder.build_compose_prompt(
            kwargs['prompt'], None
        ),
    }

    method = type_to_method.get(prompt_type)
    if not method:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    return method()


__all__ = [
    "PromptType",
    "PromptTemplates",
    "PromptBuilder",
    "prompt_builder",
    "get_prompt",
]
