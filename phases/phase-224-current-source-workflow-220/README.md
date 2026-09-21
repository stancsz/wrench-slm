# Phase 224: current-source 220-case workflow replay

This phase verifies the checked-out Wrench source through its local HTTP endpoint, client routing, proposal verifier, multi-pass verifier, and deterministic health fixture.

## Command

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from wrench_harness.server import main; main()" --mechanical-only --model-dir . --allowed-root . --host 127.0.0.1 --port 28901 --model-name wrench-current
python tools/run_wrench_case_eval.py evals/wrench-expanded-v2/cases.jsonl --endpoint http://127.0.0.1:28901/v1/chat/completions --model wrench-current --root . --output <receipt> --health-fixture --timeout 10 --startup-timeout 5
```

## Result

The endpoint completed all 220 requests. The mechanical fast path handled 220 of 220 requests with zero model calls. There were 219 outcome matches, 119 exact proposal matches, 119 of 120 eligible exact accepts, zero prohibited accepts, and zero transport or runtime abstentions. Median client latency was 0.531 ms and p95 was 49.443 ms.

The single outcome mismatch is `eval59_read_file_01_00`: the fixture asks to read `GOAL.md` with a 131072 byte ceiling, while the current repository copy exceeds that verifier limit and correctly returns `file_size_limit`. This is an environment and fixture-size mismatch, not a dense-native context result.

This is an integrated mechanical workflow diagnostic. It does not prove MiniMax teacher parity, weighted frontier-token coverage, native dense attention quality, or production readiness. The dense-native conditional target remains: if enabled, the first model-side stage must be an integrated low-cost pruner plus cherrypicker that reduces raw 2M to 4M input to a bounded 32K to 64K working context before expensive attention, with a receipt binding selected and omitted spans to the original payload hash.

## Verification

- Receipt: `evaluation.json`
- Canonical fixture SHA-256: `77ce67c7b6bb492ffc63ba26c75c322d38d73425f51e672a640705b97c78ac77`
- Source regression: `169 passed, 14 warnings`
