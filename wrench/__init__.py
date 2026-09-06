"""Wrench-SLM package surface."""

from .protocol import (  # noqa: F401
    REQUIRED_KEYS,
    ROUTER_FALLBACK,
    ValidationResult,
    canonical_json,
    exact_match,
    iter_jsonl,
    parse_call,
    target_call,
    validate_call,
)
from .fsm import JsonToolCallFSM, State, fsm_validate  # noqa: F401
from .tokenizer_fsm import TokenizerGrammar  # noqa: F401
from .policy import Prediction, ProductionDataBaseline, load_json_prediction  # noqa: F401
from .reward import RewardBreakdown, compute_reward, is_pseudo_safety_shield  # noqa: F401
from .dataset import JsonlDataset, SYSTEM_PROMPT, build_training_prompt, format_completion  # noqa: F401
from .inference import FsmLogitsProcessor, InferenceStats, LocalExecutor, benchmark, ensure_model_path  # noqa: F401
from .training import grpo_step, grpo_train, sft_train, save_lora, save_metrics, build_lora_model  # noqa: F401
from .evaluate import EvalRecord, EvalSummary, evaluate_baseline, write_summary  # noqa: F401
from .canary import CanaryResult, run_canary, write_canary  # noqa: F401
