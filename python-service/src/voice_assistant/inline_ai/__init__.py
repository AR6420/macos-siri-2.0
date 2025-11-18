"""
Inline AI module for comprehensive text processing.

This module provides on-demand text enhancement capabilities that can be triggered
from text selections across the macOS system, including:
- Rewriting (tone adjustment)
- Summarization
- Proofreading (grammar/spelling correction)
- Formatting (key points, lists, tables)
- Content composition (generation from prompts)
"""

# Core text processing
from .rewriter import TextRewriter, ToneType, RewriteResult
from .summarizer import TextSummarizer, SummaryResult
from .proofreader import TextProofreader, ProofreadResult, TextChange
from .formatter import TextFormatter, FormatResult, FormatType
from .composer import ContentComposer, ComposeResult

# Prompt management
from .prompts import (
    PromptType,
    PromptTemplates,
    PromptBuilder,
    prompt_builder,
    get_prompt,
)

__all__ = [
    # Rewriting
    "TextRewriter",
    "ToneType",
    "RewriteResult",
    # Summarization
    "TextSummarizer",
    "SummaryResult",
    # Proofreading
    "TextProofreader",
    "ProofreadResult",
    "TextChange",
    # Formatting
    "TextFormatter",
    "FormatResult",
    "FormatType",
    # Composition
    "ContentComposer",
    "ComposeResult",
    # Prompts
    "PromptType",
    "PromptTemplates",
    "PromptBuilder",
    "prompt_builder",
    "get_prompt",
]
