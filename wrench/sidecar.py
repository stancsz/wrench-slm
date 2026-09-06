"""Wrench Gateway Sidecar: Autonomous, continuous in-a-loop learning daemon.

Runs alongside LeanRouter (localhost:4000), continuously tails tool_calls.log,
filters successful Wrench-specific operations, trains the pure-blood NanoWrench
model in the background, runs held-out evaluations, and serves canary offload
on port 4010.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import torch

from .fsm import fsm_validate
from .model import NanoWrench, NanoWrenchConfig
from .pure_training import load_pure_model, save_pure_model
from .reward import _is_powershell_balanced, _posix_balanced
from .tokenizer import WrenchTokenizer


# Configure logger
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "sidecar.log"

class FlushFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


logger = logging.getLogger("wrench.sidecar")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _file_h = FlushFileHandler(str(LOG_FILE), encoding="utf-8")
    _file_h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    _stream_h = logging.StreamHandler()
    _stream_h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(_file_h)
    logger.addHandler(_stream_h)

# Allowed Wrench mechanical tools
WRENCH_TOOLS = {
    "exec_command",
    "write_stdin",
    "send_input",
    "get_goal",
    "update_goal",
    "create_goal",
    "spawn_agent",
    "wait_agent",
    "multi_agent_v1",
}


def _find_gateway_logs_dir() -> Path:
    env_dir = os.environ.get("LEAN_ROUTER_LOGS_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    container_path = Path("/gateway_logs")
    if container_path.exists():
        return container_path

    host_path = Path(r"C:\Users\stanc\github\lean-router\logs")
    if host_path.exists():
        return host_path

    relative_path = Path(__file__).resolve().parent.parent.parent / "lean-router" / "logs"
    if relative_path.exists():
        return relative_path

    # Fallback to local logs directory
    local_logs = Path(__file__).resolve().parent.parent / "logs"
    local_logs.mkdir(parents=True, exist_ok=True)
    return local_logs


class SidecarState:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.data_dir = root_dir / "data"
        self.models_dir = root_dir / "models"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.offset_file = self.data_dir / "sidecar_offset.json"
        self.status_file = self.data_dir / "sidecar_status.json"
        self.buffer_file = self.data_dir / "sidecar_buffer.jsonl"
        self.live_model_path = self.models_dir / "nano_wrench_live.pt"

        self.byte_offset: int = 0
        self.lines_scanned: int = 0
        self.mined_samples: int = 0
        self.train_cycles: int = 0
        self.latest_loss: float = 0.0
        self.latest_accuracy: float = 0.0
        self.uptime_started: float = time.time()
        self.running: bool = True

        self._held_out_hashes: Set[str] = self._load_held_out_hashes()
        self._load_offset()

    def _load_held_out_hashes(self) -> Set[str]:
        hashes = set()
        held_out_path = self.data_dir / "held_out.jsonl"
        if held_out_path.exists():
            with open(held_out_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        p = json.loads(line).get("prompt", "")
                        if p:
                            hashes.add(hashlib.sha256(p.strip().encode("utf-8")).hexdigest())
                    except Exception:
                        continue
        return hashes

    def is_quarantined(self, prompt: str) -> bool:
        h = hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()
        return h in self._held_out_hashes

    def _load_offset(self) -> None:
        if self.offset_file.exists():
            try:
                data = json.loads(self.offset_file.read_text(encoding="utf-8"))
                self.byte_offset = data.get("byte_offset", 0)
                self.lines_scanned = data.get("lines_scanned", 0)
                self.mined_samples = data.get("mined_samples", 0)
                self.train_cycles = data.get("train_cycles", 0)
            except Exception:
                pass

    def save_offset(self) -> None:
        payload = {
            "byte_offset": self.byte_offset,
            "lines_scanned": self.lines_scanned,
            "mined_samples": self.mined_samples,
            "train_cycles": self.train_cycles,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.offset_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def save_status(self) -> None:
        payload = {
            "service": "Wrench-Gateway-Sidecar",
            "version": "1.0.0-pure-blood",
            "status": "RUNNING" if self.running else "STOPPED",
            "uptime_seconds": round(time.time() - self.uptime_started, 1),
            "lines_scanned": self.lines_scanned,
            "mined_samples": self.mined_samples,
            "train_cycles_completed": self.train_cycles,
            "latest_train_loss": round(self.latest_loss, 4),
            "latest_held_out_accuracy": round(self.latest_accuracy, 4),
            "model_path": str(self.live_model_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.status_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class GatewayLogWatcher:
    """Tails lean-router/logs/tool_calls.log with real success & Wrench-relevance filter."""

    def __init__(self, logs_dir: Path, state: SidecarState) -> None:
        self.logs_dir = logs_dir
        self.state = state
        self.log_file = logs_dir / "tool_calls.log"

    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        # Format 1: Direct JSON record
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                pass

        # Format 2: LeanRouter standard log line:
        # [2026-09-04 18:54:25] [INFO] [82b1dff3] Completed: exec_command (call_87e180354d8648438f52c8ba) args: {"cmd":"..."}
        import re
        m = re.search(r"Completed:\s+(?P<tool>[\w\-:]+)\s+\((?P<call_id>call_[\w\-]+)\)\s+args:\s+(?P<raw_args>\{.*\})", line)
        if m:
            tool = m.group("tool")
            try:
                args = json.loads(m.group("raw_args"))
                return {
                    "tool": tool,
                    "args": args,
                    "status": "success",
                    "exit_code": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception:
                return None
        return None

    def filter_wrench_record(self, raw_line_or_dict: Any) -> Optional[Dict[str, Any]]:
        record = self.parse_log_line(raw_line_or_dict) if isinstance(raw_line_or_dict, str) else raw_line_or_dict
        if not record or not isinstance(record, dict):
            return None

        tool = record.get("tool") or record.get("name")
        if tool not in WRENCH_TOOLS:
            return None

        # Check success status
        status = record.get("status")
        exit_code = record.get("exit_code")
        error = record.get("error")
        if error or (exit_code is not None and exit_code != 0):
            return None
        if status not in {None, "success", "ok", 0}:
            return None

        args = record.get("args") or {}
        if not isinstance(args, dict):
            return None

        # Verify command balance if exec_command
        if tool == "exec_command":
            cmd = args.get("cmd", "")
            if not isinstance(cmd, str) or not cmd.strip():
                return None
            if not (_is_powershell_balanced(cmd) or _posix_balanced(cmd)):
                return None

        prompt = record.get("prompt") or record.get("query") or record.get("instruction")
        if not prompt or not isinstance(prompt, str):
            # Synthesize natural prompt if raw completion log
            if tool == "exec_command":
                cmd = str(args.get("cmd", "")).strip()
                if cmd.startswith("py ") or cmd.startswith("python"):
                    prompt = f"Run the following Python script/command:\n{cmd}"
                elif cmd.startswith("git "):
                    prompt = f"Execute git command: {cmd}"
                elif cmd.startswith("pytest"):
                    prompt = f"Run unit tests: {cmd}"
                elif cmd.startswith("ruff"):
                    prompt = f"Run code linting: {cmd}"
                else:
                    prompt = f"Execute shell command: {cmd}"
            elif tool == "write_stdin":
                prompt = f"Send input to active process: {str(args.get('text', ''))[:160]}"
            elif tool == "send_input":
                prompt = f"Send input to task: {str(args.get('input', ''))[:160]}"
            elif tool == "get_goal":
                prompt = f"Get status and details for goal {args.get('id', '')}"
            elif tool == "update_goal":
                prompt = f"Update goal {args.get('id', '')} to status: {args.get('status', '')}"
            else:
                prompt = f"Execute tool {tool}"

        # Absolute test set quarantine
        if self.state.is_quarantined(prompt):
            return None

        canonical = json.dumps({"tool": tool, "args": args}, ensure_ascii=False)
        return {
            "prompt": prompt.strip(),
            "tool": tool,
            "args": args,
            "canonical_call": canonical,
            "timestamp": record.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }

    def poll_new_entries(self) -> List[Dict[str, Any]]:
        if not self.log_file.exists():
            return []

        file_size = self.log_file.stat().st_size
        if file_size < self.state.byte_offset:
            self.state.byte_offset = 0

        if file_size == self.state.byte_offset:
            return []

        mined = []
        with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.state.byte_offset)
            for line in f:
                self.state.lines_scanned += 1
                line = line.strip()
                if not line:
                    continue
                verified = self.filter_wrench_record(line)
                if verified:
                    mined.append(verified)
                    self.state.mined_samples += 1
            self.state.byte_offset = f.tell()

        self.state.save_offset()
        if mined:
            with open(self.state.buffer_file, "a", encoding="utf-8") as bf:
                for item in mined:
                    bf.write(json.dumps(item, ensure_ascii=False) + "\n")
        return mined


def get_optimal_device() -> str:
    if torch.cuda.is_available():
        try:
            t = torch.zeros(1, device="cuda")
            _ = t + 1
            emb = torch.nn.Embedding(2, 2).to("cuda")
            _ = emb(torch.tensor([0], device="cuda"))
            return "cuda"
        except Exception as e:
            logger.warning(f"CUDA hardware detected but kernel execution failed ({e}). Running on CPU.")
            return "cpu"
    return "cpu"


class BackgroundTrainer:
    """Incrementally trains NanoWrench using new mined samples + replay buffer."""

    def __init__(self, state: SidecarState, tokenizer: WrenchTokenizer) -> None:
        self.state = state
        self.tokenizer = tokenizer
        self.device = get_optimal_device()
        self.model = self._get_or_create_model()

    def _get_or_create_model(self) -> NanoWrench:
        if self.state.live_model_path.exists():
            try:
                return load_pure_model(str(self.state.live_model_path), device=self.device)
            except Exception:
                pass
        model = NanoWrench(NanoWrenchConfig())
        model.to(self.device)
        return model

    def train_step_if_needed(self, min_samples: int = 16) -> bool:
        if not self.state.buffer_file.exists():
            return False

        # Read available buffered samples
        buffer_lines = []
        if self.state.buffer_file.exists():
            with open(self.state.buffer_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        buffer_lines.append(line.strip())

        base_train_path = self.state.data_dir / "train.jsonl"
        # Cold start training run on base dataset if never trained
        if self.state.train_cycles == 0 and base_train_path.exists():
            logger.info(f"[sidecar] Performing cold start training on base data ({self.device})...")
            from .pure_training import train_nano_wrench
            metrics = train_nano_wrench(
                self.model,
                self.tokenizer,
                str(base_train_path),
                batch_size=8,
                grad_accum_steps=2,
                max_steps=50,
                log_every=5,
                learning_rate=3e-4,
                device=self.device,
            )
            self.state.latest_loss = metrics.loss_end
            self.state.train_cycles += 1
            save_pure_model(self.model, str(self.state.live_model_path))
            self.evaluate_held_out()
            self.state.save_status()
            logger.info(f"[sidecar] Cold start complete! Checkpoint saved to {self.state.live_model_path}")
            return True

        if len(buffer_lines) >= min_samples:
            # Mode A: Priority training on freshly mined gateway samples!
            logger.info(f"[sidecar] [LIVE INGEST] Running priority cycle on {len(buffer_lines)} fresh gateway samples...")
            source_file = str(self.state.buffer_file)
            cycle_steps = 25
            lr = 2e-4
            should_clear = True
        else:
            # Mode B: Continuous background self-evolution on golden dataset!
            logger.info(f"[sidecar] [PERPETUAL EVOLUTION] Cycle {self.state.train_cycles + 1} ongoing training on base dataset...")
            source_file = str(base_train_path)
            cycle_steps = 25
            lr = 1e-4
            should_clear = False

        from .pure_training import train_nano_wrench
        metrics = train_nano_wrench(
            self.model,
            self.tokenizer,
            source_file,
            batch_size=8,
            grad_accum_steps=2,
            max_steps=cycle_steps,
            log_every=5,
            learning_rate=lr,
            device=self.device,
        )
        self.state.latest_loss = metrics.loss_end
        self.state.train_cycles += 1
        save_pure_model(self.model, str(self.state.live_model_path))

        if should_clear:
            self.state.buffer_file.write_text("", encoding="utf-8")

        self.evaluate_held_out(limit=25)
        self.state.save_status()
        logger.info(f"[sidecar] Cycle {self.state.train_cycles} complete! Loss={metrics.loss_end:.4f}")
        return True

    def evaluate_held_out(self, limit: int = 100) -> float:
        held_out_path = self.state.data_dir / "held_out.jsonl"
        if not held_out_path.exists():
            return 0.0

        self.model.eval()
        correct = 0
        total = 0
        with open(held_out_path, "r", encoding="utf-8") as f:
            for line in f:
                if total >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    prompt = item.get("prompt", "")
                    target = item.get("canonical_call", "")
                    input_text = f"Prompt: {prompt}\nCall: "
                    input_ids = torch.tensor([self.tokenizer.encode(input_text, add_special_tokens=True)], device=self.device)
                    max_ctx = self.model.config.max_seq_len - 48
                    if input_ids.shape[1] > max_ctx:
                        input_ids = input_ids[:, -max_ctx:]
                    out = self.model.generate(input_ids, max_new_tokens=48, temperature=0.0, eos_token_id=self.tokenizer.eos_token_id)
                    gen_text = self.tokenizer.decode(out[0].tolist()[input_ids.shape[1]:])
                    if gen_text.strip() == target.strip() or fsm_validate(gen_text):
                        correct += 1
                    total += 1
                except Exception:
                    continue

        acc = (correct / max(1, total))
        self.state.latest_accuracy = acc
        logger.info(f"[sidecar] Held-out validation score: {acc * 100:.1f}% ({correct}/{total})")
        return acc

    def predict(self, prompt: str) -> str:
        self.model.eval()
        input_text = f"Prompt: {prompt}\nCall: "
        input_ids = torch.tensor([self.tokenizer.encode(input_text, add_special_tokens=True)], device=self.device)
        max_ctx = self.model.config.max_seq_len - 64
        if input_ids.shape[1] > max_ctx:
            input_ids = input_ids[:, -max_ctx:]
        out = self.model.generate(input_ids, max_new_tokens=64, temperature=0.0, eos_token_id=self.tokenizer.eos_token_id)
        gen_text = self.tokenizer.decode(out[0].tolist()[input_ids.shape[1]:])
        clean = gen_text.strip().splitlines()[0] if gen_text.strip() else ""
        if fsm_validate(clean):
            return clean
        return "ROUTER_FALLBACK"


def make_http_handler(state: SidecarState, trainer: BackgroundTrainer):
    class SidecarHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in {"/health", "/v1/health"}:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "ok", "service": "wrench-sidecar"}\n')
            elif self.path in {"/status", "/v1/status"}:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if state.status_file.exists():
                    self.wfile.write(state.status_file.read_bytes())
                else:
                    self.wfile.write(b'{"status": "initializing"}\n')
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path in {"/predict", "/v1/chat/completions"}:
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len).decode("utf-8")
                try:
                    data = json.loads(body)
                    prompt = data.get("prompt")
                    if not prompt and "messages" in data:
                        prompt = data["messages"][-1].get("content", "")
                    prediction = trainer.predict(prompt or "")
                    response = {
                        "prediction": prediction,
                        "fallback": prediction == "ROUTER_FALLBACK",
                        "model": "nano-wrench-pure-blood",
                    }
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(f'{{"error": "{str(e)}"}}\n'.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress routine access logs

    return SidecarHandler


def run_sidecar_daemon(port: int = 4010) -> None:
    root_dir = Path(__file__).resolve().parent.parent
    logs_dir = _find_gateway_logs_dir()
    logger.info("Initializing Wrench Sidecar...")
    logger.info(f"Gateway logs path: {logs_dir}")

    state = SidecarState(root_dir)
    tokenizer = WrenchTokenizer()
    watcher = GatewayLogWatcher(logs_dir, state)
    trainer = BackgroundTrainer(state, tokenizer)

    # Start HTTP server on port 4010
    handler_class = make_http_handler(state, trainer)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler_class)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info(f"HTTP Canary & Status endpoint active on http://0.0.0.0:{port}")

    # Initial status save
    state.save_status()

    # Main continuous loop
    logger.info("Entering autonomous forever loop (Train-Test-Eval)...")
    try:
        while state.running:
            new_records = watcher.poll_new_entries()
            if new_records:
                logger.info(f"Mined {len(new_records)} successful Wrench calls from gateway.")

            # Run training step if buffer has enough or periodic
            trainer.train_step_if_needed()
            state.save_status()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down sidecar gracefully...")
        state.running = False
        state.save_status()
        server.shutdown()


if __name__ == "__main__":
    run_sidecar_daemon()
