"""Fail-closed, read-only execution boundary for Wrench proposals."""

from .core import execute_model_output, execute_proposal
from .client import execute_local_qwen
from .router import CancellationToken, ProposalRouter, RouterConfig
from .state import load_router_state, save_router_state
from .tier import TierSelectionError, select_experimental_tier
from .context import ContextAdmissionError, ContextError, ContextLedger, ContextSegment, ContextSelectionError
from .snapshot import (
    RetrievalResult,
    RetrievalStatus,
    SnapshotAdmissionError,
    SourceRecord,
    SourceSnapshot,
    create_snapshot,
    retrieve_exact,
)
from .mechanical import mechanical_route
from .handoff import build_advisor_handoff
from .worker import WrenchWorker

__all__ = [
    "CancellationToken",
    "ContextAdmissionError",
    "ContextError",
    "ContextLedger",
    "ContextSegment",
    "ContextSelectionError",
    "RetrievalResult",
    "RetrievalStatus",
    "SnapshotAdmissionError",
    "SourceRecord",
    "SourceSnapshot",
    "ProposalRouter",
    "RouterConfig",
    "TierSelectionError",
    "execute_local_qwen",
    "execute_model_output",
    "execute_proposal",
    "mechanical_route",
    "create_snapshot",
    "retrieve_exact",
    "build_advisor_handoff",
    "load_router_state",
    "save_router_state",
    "select_experimental_tier",
    "WrenchWorker",
]
