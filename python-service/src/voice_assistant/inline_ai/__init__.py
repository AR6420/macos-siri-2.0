"""
Inline AI module for text rewriting and summarization.

This module provides on-demand text enhancement capabilities that can be triggered
from text selections across the macOS system.
"""

from .rewriter import TextRewriter, ToneType
from .summarizer import TextSummarizer

__all__ = ["TextRewriter", "ToneType", "TextSummarizer"]
