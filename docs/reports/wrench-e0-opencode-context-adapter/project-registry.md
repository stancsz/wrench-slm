# OpenCode project enrollment registry

Job: `W2-NS-E0-REGISTRY-20260924`
Base: `4bd510184337dddf2b8c01844d772a8dac740516`

## Result

Added a strict `wrench.opencode-project-registry.v1` registry under an
explicitly configured Wrench data root. Only the explicit
`OpenCodeProjectRegistry.enroll_project` API creates or changes enrollment;
the module does not read repository config or infer a project from cwd or a
hook payload. Profiles bind an opaque project ID to one captured
`SourceRootBinding`, a finite normalized source path list, exclusions, fixed
`explicit-paths-v1` policy, and caps of at most 16 paths, 64 KiB per file and
512 KiB total. Store paths are derived below the configured data root from
the project ID and are not created by enrollment.

Session resolution requires an exact event/record session ID, absent or empty
`subpath`, one enrolled lexical root match, and a freshly captured root
identity matching enrollment. Unknown fields and duplicate JSON fields,
profiles, project IDs or roots fail closed. Registry writes are bounded,
canonical and atomically replaced. A bounded path walk checks each existing
descendant of the captured data root before registry reads, before returning a
derived store path, and around writes. It rejects reparse/symlink and
non-directory ancestors while allowing a not-yet-created tail for stores.
Reads compare file identity/metadata across open and post-read checks; writes
revalidate the root and ancestor chain before and after replacement. These are
path-based checks and do not make filesystem operations transactional. The
exact-token gate is explicitly `exact_gate_unavailable`; the registry does not
claim OpenCode route or tokenizer parity.

## Verification

The reviewer requested reparse containment checks for every existing
data-root descendant, root/ancestor revalidation, alias-root coverage and an
atomic-write failure case. Focused synthetic tests then passed: **20 passed**
in **4.915 seconds** using the existing CPython **3.11.16** interpreter at
`C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe`.
No packages were installed. `pytest` was unavailable in the existing Python
environments, so the focused module uses the standard-library `unittest`.

Exact command, with `PYTHONPATH=src`,
`PYTHONDONTWRITEBYTECODE=1`, and `TEMP`/`TMP` set to
`C:\wrench-slm-data\tmp\W2-NS-E0-REGISTRY-20260924\repair-unittest`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m unittest discover -s tests -p test_opencode_project_registry.py -v
```

Coverage includes explicit persistence and derived store path, session and
root matching, subpath rejection, replaced and simulated reparse roots,
malformed/unknown/duplicate registry content, path normalization and
traversal, fixed policy, file/total byte caps, source and profile count caps,
reload, and redaction of source paths from the resolved object's repr. Added
review regressions simulate reparse `opencode`, `artifacts` and
`artifacts/opencode-projects` ancestors; exercise distinct IDs using path-alias
roots; and force atomic replacement failure, verifying the prior registry
remains readable and the temporary file is removed. `git diff --check` and a
separate whitespace scan of the three untracked task files passed.

Storage remained `WITHIN_LIMIT` before, during and after the run. Pre-run
inventory was 1,714,801,998 actual bytes plus 20,103,000 reserved bytes,
including the active 20,000,000-byte job reservation. Pre-run RAM was 55.6%
free and VRAM was 15,570/16,311 MiB free (95.5%). Storage, RAM and VRAM were
checked every 500 ms while the test process was live; no inventory error or
10% reserve breach occurred. The polling loop did not retain transient
numeric samples. Post-run inventory was 1,714,805,476 actual bytes plus
20,103,000 reserved bytes; RAM was 55.5% free and VRAM was 15,572/16,311 MiB
free (95.5%). Test temp files are under the approved Wrench data root.

SHA-256:

- `src/wrench_harness/opencode_project_registry.py`:
  `A5ABAF11DFAA6549CD0F8BDB5A64DBBB3E024CA53EF9F65F4E86A53C44562D6A`
- `tests/test_opencode_project_registry.py`:
  `D1267DAD4E5D419EDD6A9949DB3E424BFC2C2ED25CF5DD43A95EE6FCADB84272`

## Limits

All test roots and registry writes were synthetic and confined to the task's
temporary directory under `C:\wrench-slm-data`. Reparse behavior was simulated
through `lstat` metadata because Windows symlink creation was unavailable in
the test environment; no actual junction escape was exercised. No real
project source was read. This job did not install, launch, load or invoke a
client or plugin; the previously installed isolated OpenCode v2.0.15 CLI
remains installed. This job made no request to localhost:4000 or any provider.
The ancestor walk plus identity/metadata rechecks reduce path-swap exposure but
cannot close every race between path-based checks and I/O. The registry does
not provide a persistent cross-process store owner, hook integration,
dispatch denial, request-lifetime pinning, or exact prompt-token parity. The
owning service must serialize registry access across processes and keep the
exact-token gate closed until the route, serializer and tokenizer are pinned
and verified.
