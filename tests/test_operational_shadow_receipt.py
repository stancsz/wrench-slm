from tools.run_operational_shadow import _receipt_digest


def test_operational_shadow_digest_uses_persisted_rows():
    rows = [
        {"action": "read_file", "status": "accepted", "elapsed_ms": 1.25},
        {"action": "health_read", "status": "abstain", "elapsed_ms": 2001.5},
    ]
    recovery = {"status": "accepted", "model_calls": 0}
    errors = []

    digest = _receipt_digest(rows, recovery, errors)
    persisted = {"rows": rows, "recovery": recovery, "errors": errors}
    assert _receipt_digest(persisted["rows"], persisted["recovery"], persisted["errors"]) == digest
