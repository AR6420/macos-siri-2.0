"""
Content composition module for generating new text from prompts.

Provides functionality to generate well-written content based on user prompts,
with optional context awareness for more relevant results.
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Any
from dataclasses import dataclass

from loguru import logger

from ..llm.base import LLMProvider, Message, MessageRole, CompletionResult
from .prompts import PromptBuilder


@dataclass
class ComposeResult:
    """Result from content composition operation."""
    prompt: str
    context: str | None
    composed_text: str
    tokens_used: int = 0
    processing_time_ms: int = 0
    success: bool = True
    error: str | None = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def word_count(self) -> int:
        """Get word count of composed text."""
        return len(self.composed_text.split())

    @property
    def char_count(self) -> int:
        """Get character count of composed text."""
        return len(self.composed_text)


class ContentComposer:
    """
    Content composition engine using LLM providers.

    Generates new content based on user prompts, with optional context
    to inform the generation. Useful for:
    - Writing emails/messages
    - Creating summaries or reports
    - Generating creative content
    - Expanding on ideas
    """

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize content composer.

        Args:
            llm_provider: Configured LLM provider instance
            config: Inline AI configuration
        """
        self.llm_provider = llm_provider
        self.config = config
        self.prompt_builder = PromptBuilder()

        # Configuration
        self.compose_config = config.get("compose", {})
        self.max_length = self.compose_config.get("max_length", 500)
        self.max_tokens = config.get("max_tokens", 1024)
        self.temperature = config.get("temperature", 0.7)

        logger.info(f"ContentComposer initialized with provider: {llm_provider}")

    async def compose(
        self,
        prompt: str,
        context: str | None = None,
        max_length: int | None = None,
        temperature: float | None = None,
        timeout_seconds: float = 15.0
    ) -> ComposeResult:
        """
        Generate content based on prompt and optional context.

        Args:
            prompt: User's content request/description
            context: Optional context to inform generation
            max_length: Maximum words in generated content (None = use config default)
            temperature: LLM temperature (None = use config default)
            timeout_seconds: Maximum time for operation

        Returns:
            ComposeResult with generated content
        """
        start_time = time.time()

        # Use defaults if not specified
        if max_length is None:
            max_length = self.max_length
        if temperature is None:
            temperature = self.temperature

        logger.info(f"Composing content from prompt ({len(prompt)} chars)")
        if context:
            logger.info(f"Using context ({len(context)} chars)")
        logger.debug(f"Prompt: {prompt[:200]}...")

        try:
            # Validate prompt
            if not prompt or len(prompt.strip()) < 3:
                return ComposeResult(
                    prompt=prompt,
                    context=context,
                    composed_text="",
                    success=False,
                    error="Prompt is too short or empty. Please provide a clear request.",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Validate prompt length
            if len(prompt) > 1000:
                logger.warning("Prompt is very long, truncating to 1000 characters")
                prompt = prompt[:1000]

            # Validate context length if provided
            if context and len(context) > 2000:
                logger.warning("Context is very long, truncating to 2000 characters")
                context = context[:2000]

            # Build the composition prompt
            composition_prompt = self.prompt_builder.build_compose_prompt(
                prompt=prompt,
                context=context
            )

            # Add length constraint if specified
            if max_length:
                composition_prompt += f"\n\nKeep the response under {max_length} words."

            # Create message for LLM
            messages = [
                Message(
                    role=MessageRole.USER,
                    content=composition_prompt
                )
            ]

            # Call LLM with timeout
            try:
                result = await asyncio.wait_for(
                    self.llm_provider.complete(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=self.max_tokens
                    ),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Composition timeout after {timeout_seconds}s")
                return ComposeResult(
                    prompt=prompt,
                    context=context,
                    composed_text="",
                    success=False,
                    error="Content composition timed out",
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # Extract composed text
            composed_text = result.content.strip()

            # Remove quotes if LLM added them
            if composed_text.startswith('"') and composed_text.endswith('"'):
                composed_text = composed_text[1:-1]
            elif composed_text.startswith("'") and composed_text.endswith("'"):
                composed_text = composed_text[1:-1]

            processing_time_ms = int((time.time() - start_time) * 1000)

            word_count = len(composed_text.split())
            char_count = len(composed_text)

            logger.info(f"Composition complete in {processing_time_ms}ms")
            logger.info(f"Generated {word_count} words, {char_count} characters")
            logger.debug(f"Composed text: {composed_text[:200]}...")

            return ComposeResult(
                prompt=prompt,
                context=context,
                composed_text=composed_text,
                tokens_used=result.tokens_used,
                processing_time_ms=processing_time_ms,
                success=True,
                metadata={
                    "word_count": word_count,
                    "char_count": char_count,
                    "has_context": context is not None,
                    "temperature": temperature,
                    "max_length": max_length
                }
            )

        except Exception as e:
            logger.exception(f"Error during composition: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)

            return ComposeResult(
                prompt=prompt,
                context=context,
                composed_text="",
                success=False,
                error=str(e),
                processing_time_ms=processing_time_ms
            )

    async def compose_email(
        self,
        prompt: str,
        context: str | None = None
    ) -> ComposeResult:
        """
        Compose an email based on prompt.

        This is a specialized composition for email format, which will
        include appropriate greeting, body, and closing.

        Args:
            prompt: Email content description (e.g., "Write a professional email...")
            context: Optional context about recipient or situation

        Returns:
            ComposeResult with email text
        """
        # Enhance prompt for email format
        enhanced_prompt = f"""Compose a professional email based on the following request.
Include an appropriate greeting, body paragraphs, and closing.

Request: {prompt}"""

        return await self.compose(
            prompt=enhanced_prompt,
            context=context,
            max_length=300,
            temperature=0.6  # Slightly lower for more professional tone
        )

    async def compose_message(
        self,
        prompt: str,
        context: str | None = None
    ) -> ComposeResult:
        """
        Compose a short message (for texting, chat, etc.).

        Args:
            prompt: Message content description
            context: Optional context about recipient or conversation

        Returns:
            ComposeResult with message text
        """
        # Enhance prompt for brief format
        enhanced_prompt = f"""Compose a brief, friendly message based on the following request.
Keep it concise and casual (suitable for text message or chat).

Request: {prompt}"""

        return await self.compose(
            prompt=enhanced_prompt,
            context=context,
            max_length=100,
            temperature=0.7
        )

    async def compose_paragraph(
        self,
        prompt: str,
        context: str | None = None
    ) -> ComposeResult:
        """
        Compose a single well-written paragraph.

        Args:
            prompt: Paragraph topic or description
            context: Optional context or background information

        Returns:
            ComposeResult with paragraph text
        """
        # Enhance prompt for paragraph format
        enhanced_prompt = f"""Write a single well-crafted paragraph based on the following topic.
Make it clear, coherent, and informative.

Topic: {prompt}"""

        return await self.compose(
            prompt=enhanced_prompt,
            context=context,
            max_length=150,
            temperature=0.6
        )

    async def expand_idea(
        self,
        idea: str,
        target_length: int = 200
    ) -> ComposeResult:
        """
        Expand a brief idea or note into fuller content.

        Args:
            idea: Brief idea or note to expand
            target_length: Target word count for expansion

        Returns:
            ComposeResult with expanded text
        """
        prompt = f"""Expand on the following idea or note, adding detail,
context, and elaboration. Make it well-structured and comprehensive.

Idea: {idea}"""

        return await self.compose(
            prompt=prompt,
            context=None,
            max_length=target_length,
            temperature=0.7
        )

    async def rewrite_with_instructions(
        self,
        text: str,
        instructions: str
    ) -> ComposeResult:
        """
        Rewrite existing text following specific instructions.

        This is different from the basic rewriter - it allows for
        custom transformation instructions.

        Args:
            text: Original text to transform
            instructions: Specific instructions for how to rewrite

        Returns:
            ComposeResult with rewritten text
        """
        prompt = f"""Rewrite the following text according to these instructions:

Instructions: {instructions}

Original text: {text}

Provide only the rewritten text:"""

        return await self.compose(
            prompt=prompt,
            context=None,
            max_length=len(text.split()) + 100,  # Allow some expansion
            temperature=0.6
        )

    async def generate_from_template(
        self,
        template_type: str,
        context: Dict[str, str]
    ) -> ComposeResult:
        """
        Generate content from a template type and context variables.

        Args:
            template_type: Type of template (e.g., "thank_you_note", "apology")
            context: Dictionary of context variables

        Returns:
            ComposeResult with generated text
        """
        # Build prompt from template type and context
        context_str = "\n".join([f"- {k}: {v}" for k, v in context.items()])

        prompt = f"""Generate a {template_type.replace('_', ' ')} using the following context:

{context_str}

Generate the complete text:"""

        return await self.compose(
            prompt=prompt,
            context=None,
            temperature=0.7
        )


__all__ = ["ContentComposer", "ComposeResult"]
