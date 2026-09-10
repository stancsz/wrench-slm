# Wrench-Pro v21 model card

## Release status

This is a release-ready LoRA adapter for the declared Wrench-Pro task scope.
It is not a standalone model. Load it with
`Qwen/Qwen2.5-0.5B-Instruct` at revision
`7ae557604adf67be50417f59c2c2f167def9a775` and verify the base file hash in
`release_manifest.json`.

## Intended use

The model maps a prompt plus the supplied Windows and PowerShell context to a
validated JSON action. The evaluated scope covers configuration and file reads,
inclusive line ranges, literal filename search, Git status, the latest Git
subject, local health reads, and review-only draft writes. It also abstains on
ambiguous requests, unsupported operations, unavailable tools, and invalid line
ranges. The packaged runtime never executes the proposed action.

## Training

V21 used 6,144 authored training rows in 192 wording families, balanced across
11 task kinds and English and Chinese. It ran 300 optimizer steps with
microbatch 2, accumulation 8, learning rate 2e-6, seed 42, and a fresh
optimizer initialized from the V20 adapter. The selected step was 200. The
adapter SHA-256 is
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.

## Evaluation

The frozen V21 evaluation set scored 440/440 exact, including 280/280 routine
cases and 160/160 fallback cases. All 11 task kinds and both languages passed,
with zero unexpected fixture filesystem changes. The independent context
release v2b suite scored 220/220 exact, including all 140 routine and 80
fallback cases. The exact packaged artifact loaded in a newly provisioned
Python 3.14 environment with PyTorch 2.9.1+cu128 and returned the quickstart
call twice using an explicit local base and an empty model cache.

Observed V21 packaged evaluation latency was 1.175 seconds at p50 and 2.466
seconds at p95 on an NVIDIA GeForce RTX 5070 Ti. These are measurements of the
authored evaluator on one Windows 11 machine, not service-level objectives.

## Limitations

The datasets are authored scenarios with generated resettable fixtures. They do
not represent production traffic and do not establish reliability on arbitrary
repositories, shells, providers, languages, or task distributions. The model
does not certify deployment, router policy, cloud failover, security, or
clinical use. CPU mode is available in the runtime but was not performance
qualified. Any merged, quantized, or converted artifact requires a new complete
evaluation.

## Reproduction

Install the pinned dependencies in `requirements.txt`, install the matching
CUDA PyTorch build, provide the exact base revision, and run:

```powershell
python inference.py --input example.json --device cuda --base-path C:\path\to\base-dependency-v1
```

The checksum manifest is verified before loading. See `EVALUATION_REPORT.md`
for the evidence paths and `LINEAGE.md` for the complete source chain.
