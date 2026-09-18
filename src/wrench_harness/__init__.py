"""Fail-closed, read-only execution boundary for Wrench proposals."""

from .core import execute_model_output, execute_proposal

__all__ = ["execute_model_output", "execute_proposal"]
