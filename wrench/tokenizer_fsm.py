"""Tokenizer-backed mask of token ids allowed at each FSM state."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Mapping, Sequence, Set

from .fsm import JsonToolCallFSM, State


class TokenizerGrammar:
    """Precompute token ids compatible with the outer Wrench grammar.

    The cache covers coarse FSM states. Decoding applies an additional live
    FSM check before accepting a candidate token, so state-specific key
    prefixes and nested JSON values remain correct.
    """

    _LINE_BREAK = {"\n", "\r", "\x0b", "\x0c"}

    def __init__(self, tokenizer) -> None:
        self.tokenizer = tokenizer
        self.vocab_size = len(tokenizer.get_vocab())
        self._allowed: Dict[int, Set[State]] = defaultdict(set)
        self._by_state: Dict[State, List[int]] = {}
        self._build()

    def _token_strings(self) -> Dict[int, str]:
        return {index: token for token, index in self.tokenizer.get_vocab().items()}

    def _build(self) -> None:
        special_tokens = set(self.tokenizer.all_special_ids or [])
        for token_id, token_str in self._token_strings().items():
            if token_id in special_tokens or not token_str:
                continue
            if any(ch in self._LINE_BREAK for ch in token_str):
                continue
            self._allowed[token_id] = self._states_for_token(token_str)

        by_state: Dict[State, Set[int]] = defaultdict(set)
        for token_id, states in self._allowed.items():
            for state in states:
                by_state[state].add(token_id)
        self._by_state = {state: sorted(ids) for state, ids in by_state.items()}

    def _states_for_token(self, token_str: str) -> Set[State]:
        legal: Set[State] = set()
        for state in State:
            if state in {State.ERROR, State.DONE}:
                continue
            fsm = JsonToolCallFSM()
            fsm.state = state
            if state is State.ARGS_KEY:
                fsm._key_rest = 'args"'
            elif state is State.TOOL_KEY:
                fsm._key_rest = 'tool"'
            if fsm.consume(token_str):
                legal.add(state)
        return legal

    def allowed_token_ids(self, state: State) -> List[int]:
        return self._by_state.get(state, [])

    def mask(self, state: State) -> Sequence[int]:
        return self._by_state.get(state, [])

    def state_index(self) -> Mapping[int, List[int]]:
        return {state.value: ids for state, ids in self._by_state.items()}

    def coverage(self) -> Dict[str, int]:
        return {state.name: len(ids) for state, ids in self._by_state.items()}
