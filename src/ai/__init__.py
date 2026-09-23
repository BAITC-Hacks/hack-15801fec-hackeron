"""Fact-grounded explanation API for computed simulator results."""

from .explanation import NarrativeModel, build_prompt, explain

__all__ = ["NarrativeModel", "build_prompt", "explain"]
