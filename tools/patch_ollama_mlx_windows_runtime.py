"""Make a copy of an Ollama MLX Windows runtime relocatable for a smoke test.

Ollama's published MLX CUDA 13 Windows DLL can contain build-machine paths for
the CUDA and cuDNN DLL directories. This tool only patches those fixed-length
ASCII path strings in a copied runtime. The original runtime is never changed.
The resulting server must be started with its working directory set to the
patched ``mlx_cuda_v13`` directory, where the bundled DLLs are available.

This is a compatibility experiment for the pinned runtime version. It is not
a general binary patcher and it must not be used to claim official Ollama
support without an end-to-end validation receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPLACEMENTS = (
    b"C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.0/bin/x64",
    b"C:/Program Files/NVIDIA/CUDNN/bin/x64",
)


def patch_fixed_path(data: bytes, old: bytes) -> tuple[bytes, int]:
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"expected one {old!r} occurrence, found {count}")
    replacement = b"." + (b"\0" * (len(old) - 1))
    return data.replace(old, replacement, 1), len(old)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-runtime", type=Path, required=True)
    parser.add_argument("--output-runtime", type=Path, required=True)
    args = parser.parse_args()

    source = args.source_runtime.resolve()
    output = args.output_runtime.resolve()
    if not (source / "ollama.exe").is_file():
        raise SystemExit(f"missing Ollama executable under {source}")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")

    shutil.copytree(source, output)
    dll = output / "lib" / "ollama" / "mlx_cuda_v13" / "mlx.dll"
    original = dll.read_bytes()
    patched = original
    widths: list[int] = []
    for old in REPLACEMENTS:
        patched, width = patch_fixed_path(patched, old)
        widths.append(width)
    dll.write_bytes(patched)

    receipt = {
        "schema": "wrench.ollama-mlx-relocation.v1",
        "source_runtime": str(source),
        "output_runtime": str(output),
        "patched_file": str(dll),
        "replacement": ".",
        "patched_path_widths": widths,
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "patched_sha256": hashlib.sha256(patched).hexdigest(),
        "working_directory_required": str(
            output / "lib" / "ollama" / "mlx_cuda_v13"
        ),
    }
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
