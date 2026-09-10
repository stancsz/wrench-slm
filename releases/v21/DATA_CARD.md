# Wrench-Pro v21 data card

## Source and purpose

All V21 rows are authored developer-tool scenarios with resettable fixtures.
They are intended to teach a narrow action protocol and are not scraped from
production logs. The training stream is isolated from the scored evaluation
families. The final context suite is evaluation-only and was generated after
the package was frozen.

## V21 training data

The dataset is `release-generalization-v21`.

- Train: 6,144 rows, 192 families, SHA-256
  `7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`.
- Development: 176 rows, 11 families, SHA-256
  `8c28cccdfb03c5fe3422b25b0e77c1ff38f2617f08d055420a5434c173be8d11`.
- Frozen evaluation: 440 rows, 11 families, SHA-256
  `67d141edf2285060584cfc663527e16052d592b12fcbd407453863427c4cb996`.
- Generator SHA-256: `bf259720627b5ed1de2b600ac4c1ef74639826e830c5f40908dbc4158a1db7db`.

Each split is balanced across English and Chinese. The train split contains
512 rows for each task kind except `lines`, which has 1,024 rows to cover the
inclusive line behavior. Invalid ranges cover zero or negative, reversed, and
beyond-EOF categories.

The semantic audit reported zero errors and zero warnings for train,
development, and evaluation. The structural preflight passed the 1,536 input
and 192 output token budgets. The exposure receipt shows every task kind and
language present at steps 100, 200, and 300, with no repeated rows before the
corpus was fully consumed.

## Independent context data

`context-release-v2b` contains 220 fresh development-only rows in 44 families,
110 English and 110 Chinese. Its split SHA-256 is
`631e9082866cb47c456ea144913cca37f5a50ee646b28a220aa7f2b0511b9680` and its
generator SHA-256 is `49824ce467e684dc61ba253ef06a244329fc499347b5421d5f98836016736413`.
It varies tool, resource, and prior-result ordering and includes decoy
resources plus quoted Unicode paths. Its semantic audit, preflight, and
executable gold checks all passed before model inference.

## Data quality and redistribution

Public-input audits verify that labels are derivable from each row's supplied
context and fixture. Gold checks validate fixture outcomes, not model quality.
The data and generator remain repository evidence rather than part of the
weight package. Do not add private production data to this package without a
new provenance and licensing review.
