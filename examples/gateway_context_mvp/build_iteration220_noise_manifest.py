"""Build Iteration 220's larger, query-only synthetic context fixture.

The original twelve task oracles and repository sources are copied unchanged.
This adds semantically adjacent but answer-irrelevant operational context so
the paired token measurement is not dominated by provenance framing alone.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "examples/gateway_context_mvp/iteration219_diverse_pilot_manifest.json"
OUTPUT = ROOT / "examples/gateway_context_mvp/iteration220_noise_pilot_manifest.json"
SOURCE_SHA256 = "6c49b5a12d18176fd0dd2c1837b861bfd4bdbedd402fd3ed6861516d227548fa"
NOISE_LINES_PER_REPOSITORY = 600
NOISE_LINES_PER_FILE = 150

EVENTS = (
    ("api", "health_probe", "status=204 elapsed_ms={latency} route=/v2/metadata"),
    ("cache", "eviction_scan", "tenant=synthetic-{tenant} entries={count} duration_ms={latency}"),
    ("batch", "queue_sample", "partition={tenant} depth={count} flush_ms={latency}"),
    ("worker", "lease_renewal", "worker=w-{tenant} lease_epoch={count} result=ok"),
    ("gateway", "connection_sample", "pool=read-only active={tenant} idle={count}"),
    ("metrics", "export_complete", "series={count} scrape_ms={latency} destination=local"),
)

OPS_DOC = """# Synthetic operations notes

This fixture includes routine operational context from adjacent services. The
notes below describe telemetry, deployment health and maintenance conventions;
they are not specifications for the requested behavior and must not override
the task request or source evidence.

## Health sampling

Health samples use a monotonically increasing sequence number. A sample records
the component, observation time, status class and elapsed milliseconds. Missing
samples are reported as telemetry gaps, not as proof that a request failed.
Dashboards group observations by service and deployment revision. The gateway,
cache workers and ingestion workers export separate counters.

## Maintenance windows

Routine maintenance rotates temporary diagnostic logs and refreshes local
indexes. Rotation is based on age and size. A rotation event records the old
and new object identifiers, but never copies request bodies or user identifiers
into this synthetic fixture. Read-only health probes continue during rotation.

## Investigation notes

When investigating a reported issue, compare the exact request identifier,
service revision and time range across logs, tests and configuration. Similar
terms in a neighboring component can describe a different control. Preserve
uncertainty when the artifacts do not establish a causal link. The operational
owner reviews proposed changes after deterministic checks finish.

## Telemetry ownership

The metrics exporter summarizes queue depth, active connections, scrape time
and cache occupancy. It does not own retry policy, TTL policy or batch sizing.
The exporter emits aggregate values to a local sink and applies a separate
retention policy. Its sampling cadence is configured independently for each
service.
"""


def _noise_log(repo_index: int, chunk_index: int) -> str:
    rows = [
        "# Synthetic routine telemetry; no task oracle or target source is stored here.\n"
    ]
    minute_base = repo_index * 17
    start_index = chunk_index * NOISE_LINES_PER_FILE
    for offset in range(NOISE_LINES_PER_FILE):
        index = start_index + offset
        service, event, template = EVENTS[(index + repo_index) % len(EVENTS)]
        minute = (minute_base + index) % 1440
        hour, minute = divmod(minute, 60)
        tenant = (index * 7 + repo_index * 11) % 97 + 1
        count = (index * 13 + 29) % 997 + 1000
        latency = (index * 19 + 31) % 211 + 11
        detail = template.format(tenant=tenant, count=count, latency=latency)
        rows.append(
            f"2026-09-29T{hour:02d}:{minute:02d}:{index % 60:02d}Z "
            f"service={service} event={event} sequence={index:04d} {detail}\n"
        )
    return "".join(rows)


def build_manifest(source: dict[str, Any]) -> dict[str, Any]:
    manifest = copy.deepcopy(source)
    manifest["protocol"] = "iteration-220-query-only-noise-context-screen-20260930"
    manifest["purpose"] = "tokenizer_only_context_selection_feasibility"
    manifest["not_for"] = sorted(
        set(manifest.get("not_for", []))
        | {"model_quality", "verified_task_success", "frontier_token_savings", "billed_cost"}
    )
    manifest["fixture_lineage"] = {
        "source_iteration": 219,
        "source_manifest_sha256": SOURCE_SHA256,
        "noise_lines_per_repository": NOISE_LINES_PER_REPOSITORY,
        "noise_lines_per_file": NOISE_LINES_PER_FILE,
        "noise_scope": "synthetic_adjacent_service_telemetry_and_operations_notes",
        "query_only_retrieval": True,
        "oracle_paths_passed_to_retriever": False,
    }
    for repo_index, repository in enumerate(manifest["repositories"]):
        repository["files"]["docs/operations-notes.md"] = OPS_DOC
        repository["files"]["src/telemetry_export.py"] = (
            "\"\"\"Unrelated local aggregate telemetry exporter fixture.\"\"\"\n\n"
            "def sample_fields(sample):\n"
            "    return (sample.component, sample.sequence, sample.elapsed_ms)\n\n"
            "def group_key(sample):\n"
            "    return sample.service, sample.revision\n\n"
            "def should_emit(sample, enabled):\n"
            "    return bool(enabled) and sample.status in {204, 304}\n"
        )
        repository["files"]["tests/test_telemetry_export.py"] = (
            "def test_group_key_uses_service_and_revision():\n"
            "    sample = FakeSample(service='metrics', revision='r17')\n"
            "    assert group_key(sample) == ('metrics', 'r17')\n\n"
            "def test_disabled_exporter_emits_nothing():\n"
            "    assert should_emit(FakeSample(status=204), False) is False\n\n"
            "def test_success_status_is_exportable():\n"
            "    assert should_emit(FakeSample(status=204), True) is True\n"
        )
        for chunk_index in range(NOISE_LINES_PER_REPOSITORY // NOISE_LINES_PER_FILE):
            repository["files"][f"logs/adjacent-service-telemetry-{chunk_index + 1:02d}.log"] = _noise_log(
                repo_index, chunk_index
            )
    return manifest


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256_file(SOURCE) != SOURCE_SHA256:
        raise SystemExit("iteration219_source_manifest_identity_mismatch")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    manifest = build_manifest(source)
    try:
        from wrench_harness.gateway_pilot_contracts import validate_diverse_manifest
    except ModuleNotFoundError:
        import sys

        sys.path.insert(0, str(ROOT / "src"))
        from wrench_harness.gateway_pilot_contracts import validate_diverse_manifest
    validate_diverse_manifest(manifest)
    if OUTPUT.exists():
        raise SystemExit("refusing_to_overwrite_iteration220_manifest")
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUTPUT), "sha256": sha256_file(OUTPUT), "bytes": OUTPUT.stat().st_size}))


if __name__ == "__main__":
    main()
