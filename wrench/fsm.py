"""Character-level & Token-level FSM for the Wrench JSON tool-call envelope.

Provides:
- WrenchToolCallFSM: Dual-order JSON state machine supporting both {"tool":..., "args":...}
  and {"args":..., "tool":...} with exact syntax and tool-name constraints.
- GrammarLogitsProcessor: Real-time logits masking processor for Grammar-Constrained Decoding.
- fsm_validate: Backward-compatible validation helper.
"""

from __future__ import annotations

import json
import string
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set

import torch

from .protocol import REQUIRED_KEYS, validate_call

_WS = {" ", "\t", "\n", "\r"}
WRENCH_TOOLS = {
    "exec_command",
    "write_stdin",
    "send_input",
    "get_goal",
    "update_goal",
    "create_goal",
    "multi_agent_v1",
    "spawn_agent",
    "wait_agent",
}


class ArgsSubstate(Enum):
    START_DICT = auto()
    EXPECT_KEY_OR_CLOSE = auto()
    IN_KEY = auto()
    EXPECT_COLON = auto()
    EXPECT_VALUE = auto()
    IN_VALUE_STRING = auto()
    IN_RAW_VALUE = auto()
    AFTER_VALUE = auto()


class FSMState(Enum):
    START = auto()
    ROOT_OPEN = auto()
    KEY_START = auto()
    
    # Branch 1: "tool" first
    KEY_TOOL_1 = auto()
    COLON_TOOL_1 = auto()
    VALUE_TOOL_1 = auto()
    COMMA_AFTER_TOOL_1 = auto()
    KEY_ARGS_1 = auto()
    COLON_ARGS_1 = auto()
    VALUE_ARGS_1 = auto()
    ROOT_CLOSE_1 = auto()
    
    # Branch 2: "args" first
    KEY_ARGS_2 = auto()
    COLON_ARGS_2 = auto()
    VALUE_ARGS_2 = auto()
    COMMA_AFTER_ARGS_2 = auto()
    KEY_TOOL_2 = auto()
    COLON_TOOL_2 = auto()
    VALUE_TOOL_2 = auto()
    ROOT_CLOSE_2 = auto()
    
    DONE = auto()
    ERROR = auto()


class WrenchToolCallFSM:
    """State machine that constrains generation strictly to valid Wrench tool call JSON."""

    def __init__(self) -> None:
        self.state: FSMState = FSMState.START
        self.args_substate: ArgsSubstate = ArgsSubstate.START_DICT
        self._key_buffer: list[str] = []
        self._tool_name_buffer: list[str] = []
        self._args_depth: int = 0
        self._in_string: bool = False
        self._escape: bool = False
        self._buffer: list[str] = []

    def clone(self) -> WrenchToolCallFSM:
        copy_fsm = WrenchToolCallFSM()
        copy_fsm.state = self.state
        copy_fsm.args_substate = self.args_substate
        copy_fsm._key_buffer = list(self._key_buffer)
        copy_fsm._tool_name_buffer = list(self._tool_name_buffer)
        copy_fsm._args_depth = self._args_depth
        copy_fsm._in_string = self._in_string
        copy_fsm._escape = self._escape
        copy_fsm._buffer = list(self._buffer)
        return copy_fsm

    @property
    def complete(self) -> bool:
        return self.state is FSMState.DONE

    @property
    def error(self) -> bool:
        return self.state is FSMState.ERROR

    @property
    def in_payload_string(self) -> bool:
        return (
            self.state in {FSMState.VALUE_ARGS_1, FSMState.VALUE_ARGS_2}
            and self.args_substate is ArgsSubstate.IN_VALUE_STRING
        )

    def allowed_characters(self) -> Set[str]:
        if self.state is FSMState.START:
            return {"{"}
        if self.state is FSMState.ROOT_OPEN:
            return {'"'}
        if self.state is FSMState.KEY_START:
            return {"t", "a"}

        # Branch 1
        if self.state is FSMState.KEY_TOOL_1:
            idx = len(self._key_buffer)
            target = "tool\""
            return {target[idx]} if idx < len(target) else set()
        if self.state is FSMState.COLON_TOOL_1:
            return {":"}
        if self.state is FSMState.VALUE_TOOL_1:
            if not self._in_string:
                return {'"'}
            pfx = "".join(self._tool_name_buffer)
            allowed = set()
            for t in WRENCH_TOOLS:
                if t.startswith(pfx):
                    if len(t) > len(pfx):
                        allowed.add(t[len(pfx)])
                    elif len(t) == len(pfx):
                        allowed.add('"')
            return allowed
        if self.state is FSMState.COMMA_AFTER_TOOL_1:
            return {","}
        if self.state is FSMState.KEY_ARGS_1:
            if len(self._key_buffer) == 0:
                return {'"'}
            target = '"args"'
            idx = len(self._key_buffer)
            return {target[idx]} if idx < len(target) else set()
        if self.state is FSMState.COLON_ARGS_1:
            return {":"}
        if self.state is FSMState.ROOT_CLOSE_1:
            return {"}"}

        # Branch 2
        if self.state is FSMState.KEY_ARGS_2:
            idx = len(self._key_buffer)
            target = "args\""
            return {target[idx]} if idx < len(target) else set()
        if self.state is FSMState.COLON_ARGS_2:
            return {":"}
        if self.state is FSMState.COMMA_AFTER_ARGS_2:
            return {","}
        if self.state is FSMState.KEY_TOOL_2:
            if len(self._key_buffer) == 0:
                return {'"'}
            target = '"tool"'
            idx = len(self._key_buffer)
            return {target[idx]} if idx < len(target) else set()
        if self.state is FSMState.COLON_TOOL_2:
            return {":"}
        if self.state is FSMState.VALUE_TOOL_2:
            if not self._in_string:
                return {'"'}
            pfx = "".join(self._tool_name_buffer)
            allowed = set()
            for t in WRENCH_TOOLS:
                if t.startswith(pfx):
                    if len(t) > len(pfx):
                        allowed.add(t[len(pfx)])
                    elif len(t) == len(pfx):
                        allowed.add('"')
            return allowed
        if self.state is FSMState.ROOT_CLOSE_2:
            return {"}"}

        # Args parsing
        if self.state in {FSMState.VALUE_ARGS_1, FSMState.VALUE_ARGS_2}:
            sub = self.args_substate
            if sub is ArgsSubstate.START_DICT:
                return {"{"}
            if sub is ArgsSubstate.EXPECT_KEY_OR_CLOSE:
                return {'"', "}"}
            if sub is ArgsSubstate.IN_KEY:
                return set(string.ascii_letters) | set(string.digits) | {"_", "-", '"'}
            if sub is ArgsSubstate.EXPECT_COLON:
                return {":"}
            if sub is ArgsSubstate.EXPECT_VALUE:
                digits = set(string.digits) | {"-", "t", "f", "n", "[", "{"}
                return {'"'} | digits
            if sub is ArgsSubstate.IN_VALUE_STRING:
                if self._escape:
                    return set('"\\/bfnrtu') | set(string.digits) | set("abcdefABCDEF")
                return {'"', "\\"}
            if sub is ArgsSubstate.IN_RAW_VALUE:
                return set(string.digits) | {".", "e", "E", "+", "-", ",", "}", "]"}
            if sub is ArgsSubstate.AFTER_VALUE:
                return {",", "}"}

        if self.state is FSMState.DONE:
            return set()
        return set()

    def accept(self, char: str) -> bool:
        if len(char) != 1 or self.state in {FSMState.ERROR, FSMState.DONE}:
            return False

        if self.in_payload_string:
            if self._escape:
                if char not in set('"\\/bfnrtu') | set(string.digits) | set("abcdefABCDEF"):
                    self.state = FSMState.ERROR
                    return False
            else:
                if ord(char) < 32 and char != "\t":
                    self.state = FSMState.ERROR
                    return False
        else:
            if char in _WS:
                return False
            if char not in self.allowed_characters():
                self.state = FSMState.ERROR
                return False

        self._buffer.append(char)

        if self.state is FSMState.START:
            if char == "{":
                self.state = FSMState.ROOT_OPEN
        elif self.state is FSMState.ROOT_OPEN:
            if char == '"':
                self.state = FSMState.KEY_START
        elif self.state is FSMState.KEY_START:
            if char == "t":
                self.state = FSMState.KEY_TOOL_1
                self._key_buffer = ["t"]
            elif char == "a":
                self.state = FSMState.KEY_ARGS_2
                self._key_buffer = ["a"]

        # Branch 1
        elif self.state is FSMState.KEY_TOOL_1:
            self._key_buffer.append(char)
            if "".join(self._key_buffer) == 'tool"':
                self.state = FSMState.COLON_TOOL_1
        elif self.state is FSMState.COLON_TOOL_1:
            if char == ":":
                self.state = FSMState.VALUE_TOOL_1
                self._in_string = False
                self._tool_name_buffer = []
        elif self.state is FSMState.VALUE_TOOL_1:
            if char == '"':
                if not self._in_string:
                    self._in_string = True
                else:
                    self._in_string = False
                    self.state = FSMState.COMMA_AFTER_TOOL_1
            else:
                self._tool_name_buffer.append(char)
        elif self.state is FSMState.COMMA_AFTER_TOOL_1:
            if char == ",":
                self.state = FSMState.KEY_ARGS_1
                self._key_buffer = []
        elif self.state is FSMState.KEY_ARGS_1:
            self._key_buffer.append(char)
            if "".join(self._key_buffer) == '"args"':
                self.state = FSMState.COLON_ARGS_1
        elif self.state is FSMState.COLON_ARGS_1:
            if char == ":":
                self.state = FSMState.VALUE_ARGS_1
                self.args_substate = ArgsSubstate.START_DICT
                self._args_depth = 0
        elif self.state is FSMState.ROOT_CLOSE_1:
            if char == "}":
                self.state = FSMState.DONE

        # Branch 2
        elif self.state is FSMState.KEY_ARGS_2:
            self._key_buffer.append(char)
            if "".join(self._key_buffer) == 'args"':
                self.state = FSMState.COLON_ARGS_2
        elif self.state is FSMState.COLON_ARGS_2:
            if char == ":":
                self.state = FSMState.VALUE_ARGS_2
                self.args_substate = ArgsSubstate.START_DICT
                self._args_depth = 0
        elif self.state is FSMState.COMMA_AFTER_ARGS_2:
            if char == ",":
                self.state = FSMState.KEY_TOOL_2
                self._key_buffer = []
        elif self.state is FSMState.KEY_TOOL_2:
            self._key_buffer.append(char)
            if "".join(self._key_buffer) == '"tool"':
                self.state = FSMState.COLON_TOOL_2
        elif self.state is FSMState.COLON_TOOL_2:
            if char == ":":
                self.state = FSMState.VALUE_TOOL_2
                self._in_string = False
                self._tool_name_buffer = []
        elif self.state is FSMState.VALUE_TOOL_2:
            if char == '"':
                if not self._in_string:
                    self._in_string = True
                else:
                    self._in_string = False
                    self.state = FSMState.ROOT_CLOSE_2
            else:
                self._tool_name_buffer.append(char)
        elif self.state is FSMState.ROOT_CLOSE_2:
            if char == "}":
                self.state = FSMState.DONE

        # Value Args logic for both branches
        if self.state in {FSMState.VALUE_ARGS_1, FSMState.VALUE_ARGS_2}:
            sub = self.args_substate
            if sub is ArgsSubstate.START_DICT:
                if char == "{":
                    self._args_depth = 1
                    self.args_substate = ArgsSubstate.EXPECT_KEY_OR_CLOSE
            elif sub is ArgsSubstate.EXPECT_KEY_OR_CLOSE:
                if char == '"':
                    self.args_substate = ArgsSubstate.IN_KEY
                    self._escape = False
                elif char == "}":
                    self._args_depth -= 1
                    if self._args_depth == 0:
                        self.state = (
                            FSMState.ROOT_CLOSE_1
                            if self.state is FSMState.VALUE_ARGS_1
                            else FSMState.COMMA_AFTER_ARGS_2
                        )
            elif sub is ArgsSubstate.IN_KEY:
                if char == '"':
                    self.args_substate = ArgsSubstate.EXPECT_COLON
            elif sub is ArgsSubstate.EXPECT_COLON:
                if char == ":":
                    self.args_substate = ArgsSubstate.EXPECT_VALUE
            elif sub is ArgsSubstate.EXPECT_VALUE:
                if char == '"':
                    self.args_substate = ArgsSubstate.IN_VALUE_STRING
                    self._escape = False
                elif char == "{":
                    self._args_depth += 1
                    self.args_substate = ArgsSubstate.EXPECT_KEY_OR_CLOSE
                elif char in string.digits or char in "-tf":
                    self.args_substate = ArgsSubstate.IN_RAW_VALUE
            elif sub is ArgsSubstate.IN_VALUE_STRING:
                if self._escape:
                    self._escape = False
                elif char == "\\":
                    self._escape = True
                elif char == '"':
                    self.args_substate = ArgsSubstate.AFTER_VALUE
            elif sub is ArgsSubstate.IN_RAW_VALUE:
                if char == ",":
                    self.args_substate = ArgsSubstate.EXPECT_KEY_OR_CLOSE
                elif char == "}":
                    self._args_depth -= 1
                    if self._args_depth == 0:
                        self.state = (
                            FSMState.ROOT_CLOSE_1
                            if self.state is FSMState.VALUE_ARGS_1
                            else FSMState.COMMA_AFTER_ARGS_2
                        )
                    else:
                        self.args_substate = ArgsSubstate.AFTER_VALUE
            elif sub is ArgsSubstate.AFTER_VALUE:
                if char == ",":
                    self.args_substate = ArgsSubstate.EXPECT_KEY_OR_CLOSE
                elif char == "}":
                    self._args_depth -= 1
                    if self._args_depth == 0:
                        self.state = (
                            FSMState.ROOT_CLOSE_1
                            if self.state is FSMState.VALUE_ARGS_1
                            else FSMState.COMMA_AFTER_ARGS_2
                        )

        return True

    def consume(self, text: str) -> bool:
        for c in text:
            if not self.accept(c):
                return False
        return True

    def validate(self) -> bool:
        text = "".join(self._buffer).strip()
        try:
            value = json.loads(text)
        except Exception:
            return False
        return validate_call(value).valid and set(value) == REQUIRED_KEYS


class GrammarLogitsProcessor:
    """Fast, zero-overhead grammar constrained decoding processor for Wrench tokens."""

    def __init__(self, tokenizer: Any) -> None:
        self.tokenizer = tokenizer
        self.vocab_size = tokenizer.vocab_size
        self.eos_token_id = tokenizer.eos_token_id

        # Precompute string decoded for all tokens in vocab
        self.token_strings: list[str] = []
        self.valid_tokens: list[int] = []
        self.clean_payload_mask = torch.zeros(self.vocab_size, dtype=torch.bool)
        self.special_payload_token_ids: list[int] = []

        for i in range(self.vocab_size):
            if i == self.eos_token_id:
                self.token_strings.append("<eos>")
            elif hasattr(tokenizer, "_id_to_bytes") and i in tokenizer._id_to_bytes:
                try:
                    s = tokenizer.decode([i], skip_special_tokens=False)
                    self.token_strings.append(s)
                except Exception:
                    self.token_strings.append("")
            elif i < 256:
                try:
                    s = tokenizer.decode([i], skip_special_tokens=False)
                    self.token_strings.append(s)
                except Exception:
                    self.token_strings.append("")
            else:
                self.token_strings.append("")

        special_set = {
            tokenizer.pad_token_id,
            tokenizer.bos_token_id,
            tokenizer.eos_token_id,
            getattr(tokenizer, "fallback_token_id", -1),
        }

        for i in range(min(self.vocab_size, 512)):
            s = self.token_strings[i]
            if not s or i in special_set:
                continue
            self.valid_tokens.append(i)
            if any(c in s for c in ['"', '\\', '\n', '\r']):
                self.special_payload_token_ids.append(i)
            else:
                self.clean_payload_mask[i] = True

    def __call__(self, current_ids: list[int], logits: torch.Tensor) -> torch.Tensor:
        current_text = self.tokenizer.decode(current_ids, skip_special_tokens=True)
        fsm = WrenchToolCallFSM()
        if not fsm.consume(current_text):
            return logits

        if fsm.complete:
            constrained = torch.full_like(logits, -float("inf"))
            constrained[:, self.eos_token_id] = logits[:, self.eos_token_id]
            return constrained

        mask = torch.zeros(self.vocab_size, dtype=torch.bool, device=logits.device)
        in_str = fsm.in_payload_string

        if in_str:
            mask |= self.clean_payload_mask.to(logits.device)
            for tid in self.special_payload_token_ids:
                tfsm = fsm.clone()
                if tfsm.consume(self.token_strings[tid]):
                    mask[tid] = True
        else:
            allowed_chars = fsm.allowed_characters()
            for tid in self.valid_tokens:
                token_str = self.token_strings[tid]
                first_c = token_str[0]
                if first_c not in allowed_chars:
                    continue
                if len(token_str) > 1:
                    tfsm = fsm.clone()
                    if tfsm.consume(token_str):
                        mask[tid] = True
                else:
                    mask[tid] = True

        if mask.any():
            logits[:, ~mask] = -float("inf")
        return logits


class State(Enum):
    START = auto()
    TOOL_KEY = auto()
    TOOL_COLON = auto()
    TOOL_STRING = auto()
    AFTER_TOOL = auto()
    ARGS_KEY = auto()
    ARGS_COLON = auto()
    ARGS_OBJECT = auto()
    DONE = auto()
    ERROR = auto()


_TOOL_REST = 'tool"'
_ARGS_REST = 'args"'
_WS_SINGLE = {" ", "\t", "\n", "\r"}


class JsonToolCallFSM:
    """Incrementally constrain the exact ``{"tool": ..., "args": ...}`` envelope."""

    def __init__(self) -> None:
        self.state: State = State.START
        self._key_rest: str = _TOOL_REST
        self._key_index: int = 0
        self._in_string: bool = False
        self._escape: bool = False
        self._args_depth: int = 0
        self._args_in_string: bool = False
        self._args_escape: bool = False
        self._buffer: list[str] = []

    @property
    def complete(self) -> bool:
        return self.state is State.DONE

    @property
    def error(self) -> bool:
        return self.state is State.ERROR

    def reset(self) -> None:
        self.__init__()

    def _expected_characters(self) -> set[str]:
        if self.state is State.START:
            return {"{"} | _WS_SINGLE
        if self.state in {State.TOOL_KEY, State.ARGS_KEY}:
            if self._key_index == 0:
                return {'"'} | _WS_SINGLE
            return {self._key_rest[self._key_index - 1]}
        if self.state in {State.TOOL_COLON, State.ARGS_COLON}:
            return {":"} | _WS_SINGLE
        if self.state is State.AFTER_TOOL:
            return {","} | _WS_SINGLE
        if self.state is State.TOOL_STRING:
            if self._escape:
                return set('"\\/bfnrtu') | set(string.digits) | set("abcdefABCDEF")
            if self._in_string:
                return set(string.printable) - {"\n", "\r"} | {'"', "\\"}
            return {'"'} | _WS_SINGLE
        if self.state is State.ARGS_OBJECT:
            if self._args_in_string:
                if self._args_escape:
                    return set('"\\/bfnrtu') | set(string.digits) | set("abcdefABCDEF")
                return set(string.printable) - {"\n", "\r"} | {'"', "\\"}
            return set(string.printable) - {"\n", "\r"}
        return set()

    def allowed_characters(self) -> set[str]:
        return self._expected_characters()

    def accept(self, char: str) -> bool:
        if len(char) != 1 or self.state in {State.ERROR, State.DONE}:
            return False
        if char not in self.allowed_characters():
            self.state = State.ERROR
            return False
        self._buffer.append(char)
        if char in _WS_SINGLE and not self._in_string and not self._args_in_string:
            return True

        if self.state is State.START:
            self.state = State.TOOL_KEY
        elif self.state in {State.TOOL_KEY, State.ARGS_KEY}:
            if self._key_index == 0:
                self._key_index = 1
            else:
                self._key_index += 1
                if self._key_index > len(self._key_rest):
                    if self.state is State.TOOL_KEY:
                        self.state = State.TOOL_COLON
                    else:
                        self.state = State.ARGS_COLON
                    self._key_index = 0
                    self._key_rest = ""
        elif self.state is State.TOOL_COLON:
            self.state = State.TOOL_STRING
            self._in_string = False
        elif self.state is State.TOOL_STRING:
            if self._escape:
                self._escape = False
            elif char == "\\":
                self._escape = True
            elif char == '"':
                if self._in_string:
                    self._in_string = False
                    self.state = State.AFTER_TOOL
                else:
                    self._in_string = True
        elif self.state is State.AFTER_TOOL:
            self.state = State.ARGS_KEY
            self._key_rest = _ARGS_REST
            self._key_index = 0
        elif self.state is State.ARGS_COLON:
            self.state = State.ARGS_OBJECT
        elif self.state is State.ARGS_OBJECT:
            if self._args_escape:
                self._args_escape = False
            elif self._args_in_string and char == "\\":
                self._args_escape = True
            elif char == '"':
                self._args_in_string = not self._args_in_string
            elif not self._args_in_string and char == "{":
                self._args_depth += 1
            elif not self._args_in_string and char == "}":
                if self._args_depth == 0:
                    self.state = State.DONE
                else:
                    self._args_depth -= 1
        return True

    def consume(self, text: str) -> bool:
        return all(self.accept(char) for char in text)

    def validate(self) -> bool:
        if not self.complete:
            return False
        try:
            value = json.loads("".join(self._buffer))
        except json.JSONDecodeError:
            return False
        return validate_call(value).valid and set(value) == REQUIRED_KEYS

    def constrained_prefix(self, text: str) -> str:
        fresh = JsonToolCallFSM()
        for char in text:
            if not fresh.accept(char):
                break
        return "".join(fresh._buffer)


def fsm_validate(text: str) -> bool:
    """Validate a complete JSON tool call against the grammar."""
    fsm = JsonToolCallFSM()
    if not fsm.consume(text):
        return False
    return fsm.validate()

