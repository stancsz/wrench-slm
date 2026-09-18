"""Fail-closed, read-only execution boundary for Wrench proposals."""

from .core import execute_model_output, execute_proposal
from .client import execute_local_qwen

__all__ = ["execute_local_qwen", "execute_model_output", "execute_proposal"]
