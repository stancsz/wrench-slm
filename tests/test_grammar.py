"""Tokenizer grammar coverage tests (CPU only)."""
from __future__ import annotations

import time

from wrench import State


def _build_minimal_tokenizer():
    """Build a tiny in-memory tokenizer for grammar coverage checks."""
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace

    vocab = {
        "<pad>": 0,
        "{": 1,
        "}": 2,
        ",": 3,
        ":": 4,
        '"': 5,
        '"tool"': 6,
        '"args"': 7,
        "tool": 8,
        "name": 9,
        "cmd": 10,
        "ls": 11,
        '"ls"': 12,
        " ": 13,
    }
    tokenizer = Tokenizer(WordLevel(vocab=vocab, unk_token=None))
    tokenizer.pre_tokenizer = Whitespace()
    return tokenizer


def test_fsm_state_machine_has_full_states():
    names = {state.name for state in State}
    assert {"START", "TOOL_KEY", "TOOL_STRING", "ARGS_KEY", "ARGS_OBJECT", "DONE", "ERROR"} <= names


def test_grammar_allows_at_least_one_token_per_state():
    from wrench.tokenizer_fsm import TokenizerGrammar

    class StubTokenizer:
        def get_vocab(self):
            return {"{": 1, '"tool"': 2, ":": 3, '"foo"': 4, ",": 5, '"args"': 6, '"bar"': 7, "}": 8}

        all_special_ids: list[int] = []

    grammar = TokenizerGrammar(StubTokenizer())
    coverage = grammar.coverage()
    for state_name in ("START", "TOOL_KEY", "ARGS_KEY", "ARGS_OBJECT", "DONE"):
        assert coverage.get(state_name, 0) > 0 or state_name == "DONE"


def test_grammar_mask_latency_is_sub_millisecond():
    from wrench.tokenizer_fsm import TokenizerGrammar

    class StubTokenizer:
        vocab = {
            "{": 1, "}": 2, ",": 3, ":": 4, '"': 5, '"tool"': 6, '"args"': 7,
            '"foo"': 8, '"bar"': 9, "cmd": 10, "name": 11, "ls": 12,
        }

        def get_vocab(self):
            return self.vocab

        all_special_ids: list[int] = []

    grammar = TokenizerGrammar(StubTokenizer())
    started = time.perf_counter()
    for _ in range(2000):
        for state in State:
            grammar.allowed_token_ids(state)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    per_call = elapsed_ms / (2000 * len(State))
    assert per_call < 0.1
