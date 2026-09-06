"""Native Domain-Specific Byte/Subword Tokenizer for Wrench-SLM.

Designed specifically for fast, lossless encoding of JSON envelopes,
shell commands, and arbitrary developer text with zero external dependencies.
"""

from __future__ import annotations

from typing import Dict, List, Optional


SPECIAL_TOKENS = {
    "<pad>": 256,
    "<bos>": 257,
    "<eos>": 258,
    "<fallback>": 259,
}

COMMON_SUBWORDS = [
    # High-frequency JSON envelope patterns
    '{"tool": "',
    '", "args": {',
    '"cmd": "',
    '"input": "',
    '"text": "',
    '"path": "',
    '"args": {}',
    '"status": "',
    '{"tool": "exec_command", "args": {"cmd": "',
    '{"tool": "write_stdin", "args": {"input": "',
    '{"tool": "get_goal", "args": {}}',
    '{"tool": "update_goal", "args": {"status": "',
    # Tool names
    "exec_command",
    "write_stdin",
    "send_input",
    "get_goal",
    "update_goal",
    "create_goal",
    "multi_agent_v1",
    "spawn_agent",
    "wait_agent",
    "apply_patch",
    "write_file",
    "edit_file",
    # Common CLI commands & flags
    "git status",
    "git diff",
    "git log",
    "git commit",
    "git add",
    "git checkout",
    "pytest",
    "ruff check",
    "python",
    "powershell",
    "bash",
    "head -n",
    "cat ",
    "ls -la",
    "mkdir",
    "rm -rf",
    "cd ",
    "npm test",
    "cargo check",
    " --oneline",
    " --help",
    " -m ",
    " && ",
    " | ",
    # JSON syntax fragments
    '": "',
    '", "',
    '": {',
    '}}',
    '"}',
    '",',
    '":',
    ' {"',
]


class WrenchTokenizer:
    """Byte-level tokenizer with custom domain subwords for Wrench."""

    def __init__(self, target_vocab_size: int = 4096) -> None:
        self.target_vocab_size = target_vocab_size
        self.pad_token_id = SPECIAL_TOKENS["<pad>"]
        self.bos_token_id = SPECIAL_TOKENS["<bos>"]
        self.eos_token_id = SPECIAL_TOKENS["<eos>"]
        self.fallback_token_id = SPECIAL_TOKENS["<fallback>"]

        self._str_to_id: Dict[str, int] = {}
        self._id_to_bytes: Dict[int, bytes] = {}

        # 0..255: raw bytes
        for b in range(256):
            self._id_to_bytes[b] = bytes([b])

        # 256..259: special tokens
        for name, idx in SPECIAL_TOKENS.items():
            self._str_to_id[name] = idx
            self._id_to_bytes[idx] = name.encode("utf-8")

        # 260..: common subwords sorted by length descending for greedy longest-match
        curr_id = 260
        self._subwords: List[tuple[str, bytes, int]] = []
        for word in sorted(set(COMMON_SUBWORDS), key=len, reverse=True):
            if curr_id >= target_vocab_size:
                break
            b_val = word.encode("utf-8")
            self._str_to_id[word] = curr_id
            self._id_to_bytes[curr_id] = b_val
            self._subwords.append((word, b_val, curr_id))
            curr_id += 1

        self.vocab_size = target_vocab_size

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        if not text:
            return [self.bos_token_id, self.eos_token_id] if add_special_tokens else []

        tokens: List[int] = []
        if add_special_tokens:
            tokens.append(self.bos_token_id)

        raw_bytes = text.encode("utf-8")
        i = 0
        n = len(raw_bytes)
        while i < n:
            matched = False
            # Try matching longest known subword
            for _, b_sub, token_id in self._subwords:
                sub_len = len(b_sub)
                if i + sub_len <= n and raw_bytes[i : i + sub_len] == b_sub:
                    tokens.append(token_id)
                    i += sub_len
                    matched = True
                    break
            if not matched:
                tokens.append(raw_bytes[i])
                i += 1

        if add_special_tokens:
            tokens.append(self.eos_token_id)
        return tokens

    def decode(self, tokens: List[int], skip_special_tokens: bool = True) -> str:
        out_bytes = bytearray()
        special_ids = {self.pad_token_id, self.bos_token_id, self.eos_token_id, self.fallback_token_id}
        for t in tokens:
            if skip_special_tokens and t in special_ids:
                continue
            if t in self._id_to_bytes:
                out_bytes.extend(self._id_to_bytes[t])
            elif t < 256:
                out_bytes.append(t)
        return out_bytes.decode("utf-8", errors="replace")

    def __call__(self, text: str, return_tensors: Optional[str] = None):
        ids = self.encode(text, add_special_tokens=True)
        if return_tensors == "pt":
            import torch
            return {"input_ids": torch.tensor([ids], dtype=torch.long)}
        return {"input_ids": ids}
