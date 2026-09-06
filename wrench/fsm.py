"""Character-level FSM for the Wrench JSON tool-call envelope.

Tokenizer-agnostic on purpose. The model tokenizer can map each allowed
character set to token ids, so this grammar is the single source of truth
for both CPU validation and the decoding logits processor.
"""

from __future__ import annotations

import json
import string
from enum import Enum, auto

from .protocol import REQUIRED_KEYS, validate_call


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


_WS = {" ", "\t"}
_TOOL_REST = 'tool"'
_ARGS_REST = 'args"'


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
            return {"{"}
        if self.state in {State.TOOL_KEY, State.ARGS_KEY}:
            if self._key_index == 0:
                return {'"'} | _WS
            return {self._key_rest[self._key_index - 1]}
        if self.state in {State.TOOL_COLON, State.ARGS_COLON}:
            return {":"} | _WS
        if self.state is State.AFTER_TOOL:
            return {","} | _WS
        if self.state is State.TOOL_STRING:
            if self._escape:
                return set('"\\/bfnrtu') | set(string.digits) | set("abcdefABCDEF")
            if self._in_string:
                return set(string.printable) - {"\n", "\r"} | {'"', "\\"}
            return {'"'} | _WS
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
        if char in _WS:
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
