# Local intake for real Wrench abstention requests

The authored 5,600-case suite exposed a large accuracy gap, but repeated
training against its patterns would not establish production quality. Current
Wrench trace receipts retain request hashes and outcomes, not the request
text needed to fit a classifier. A future training round needs separately
approved, redacted request text and reviewed binary labels from actual Wrench
workflows. No such corpus was available in this run.

Put a UTF-8 JSONL file under this checkout's ignored `data/private/` folder.
Each line has exactly these fields:

```json
{"request_id":"opaque-local-id","workflow_id":"same-id-for-one-workflow","prompt":"Redacted request text","label":"abstain","redacted":true,"source":"real_wrench","label_source":"human_review"}
```

`label` is `abstain` or `not_abstain`. `not_abstain` means the request is
eligible for one bounded Wrench proposal. It does not authorize execution or
skip the independent verifier. Use `label_source` of `human_review` or
`verified_oracle`. `source` and `redacted` are assertions by the data provider;
the intake tool cannot prove that the text came from a real workflow or that
redaction and labeling are complete. Review these before intake. Keep related
requests in the same `workflow_id`, including retries and paraphrases.

From the repository root:

```powershell
python tools/intake_system_one_real_requests.py `
  --input data/private/real_wrench_labeled.jsonl `
  --output data/private/system_one_intake_v1
```

The command requires at least 40 distinct prompts from 20 workflows and both
labels. It rejects malformed rows, duplicate IDs, conflicting duplicate
labels, several common secret and email patterns, and exact normalized
overlap with the frozen 5,600-case suite. It removes same-label duplicate
prompts and splits by hashed workflow ID into `fit` (70%), `calibration`
(15%), and `sealed` (15%). Each split must contain both labels. The split
percentages are hash buckets, so the actual proportions can differ. The
output stays under gitignored `data/private/`; the console and manifest contain
counts and hashes, not prompts or original IDs. The processed JSONL files
still contain the redacted prompt text. The scanner is limited and does not
replace manual privacy review.

Do not train, tune, inspect labels, or select candidates with `sealed.jsonl`.
Use it once after freezing a candidate and evaluation protocol. Keep the
previously frozen `phases/system-one-binary-5k-20260922/cases.jsonl` out of
all training. These splits are procedural, not cryptographically sealed.
Future evaluation must also report false Wrench decisions, false abstentions,
balanced accuracy, per-workflow uncertainty, and warm and cold decision speed
on named hardware. Learned routing remains disabled until the broader Wrench
production gates pass.
