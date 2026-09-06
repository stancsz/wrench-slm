"""Tests for Native NanoWrench architecture and Gateway Sidecar."""

from __future__ import annotations

from pathlib import Path
import torch

from wrench.model import NanoWrench, NanoWrenchConfig
from wrench.tokenizer import WrenchTokenizer
from wrench.sidecar import GatewayLogWatcher, SidecarState


def test_nano_wrench_initialization_and_forward():
    config = NanoWrenchConfig(dim=128, n_layers=2, n_heads=4, intermediate_dim=256, max_seq_len=128)
    model = NanoWrench(config)
    assert model.num_parameters > 0

    x = torch.randint(0, config.vocab_size, (2, 16))
    logits, loss = model(x, labels=x)
    assert logits.shape == (2, 16, config.vocab_size)
    assert loss is not None
    assert loss.item() > 0.0


def test_wrench_tokenizer_lossless_roundtrip():
    tok = WrenchTokenizer()
    sample = '{"tool": "exec_command", "args": {"cmd": "pytest tests/unit/"}}'
    encoded = tok.encode(sample, add_special_tokens=True)
    decoded = tok.decode(encoded, skip_special_tokens=True)
    assert decoded == sample


def test_sidecar_log_parsing_and_filter(tmp_path: Path):
    state = SidecarState(tmp_path)
    watcher = GatewayLogWatcher(tmp_path, state)

    # Valid completed command
    line = '[2026-09-06 10:00:00] [INFO] [req123] Completed: exec_command (call_abc) args: {"cmd":"git status"}'
    res = watcher.filter_wrench_record(line)
    assert res is not None
    assert res["tool"] == "exec_command"
    assert res["args"]["cmd"] == "git status"

    # Non-Wrench tool rejection
    non_wrench = '[2026-09-06 10:00:00] [INFO] [req124] Completed: browse_web (call_def) args: {"url":"http://foo"}'
    assert watcher.filter_wrench_record(non_wrench) is None

    # Unbalanced command rejection
    unbalanced = '[2026-09-06 10:00:00] [INFO] [req125] Completed: exec_command (call_ghi) args: {"cmd":"git commit -m \'unclosed"}'
    assert watcher.filter_wrench_record(unbalanced) is None
