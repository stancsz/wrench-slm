from examples.gateway_context_mvp.run_code_task_local_mvp_iter211 import resource_sample_from_bytes


def test_torch_resource_sample_fractions_use_exact_byte_counts() -> None:
    sample = resource_sample_from_bytes(3, 10, 1_073_741_824, 4_294_967_296)
    assert sample["ram_free_fraction"] == 0.3
    assert sample["vram_free_fraction"] == 0.25
    assert sample["vram_free_mib"] == 1024


def test_torch_resource_sample_rejects_invalid_or_incoherent_values() -> None:
    for values, expected in (
        ((1, 1, 0, 0), "totals_must_be_positive"),
        ((11, 10, 1, 4), "out_of_range"),
        ((True, 10, 1, 4), "integers"),
    ):
        try:
            resource_sample_from_bytes(*values)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"expected ValueError containing {expected}")
