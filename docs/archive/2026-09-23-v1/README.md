# V1 direction preserved before v2 realignment

Snapshot source commit: `87909b958ac252b0b3b2cc720a300babb26b733d`. These
copies include the working-tree documentation edits present before this
realignment, not just the committed versions.

[Snapshot manifest](snapshot-manifest.json) binds exact bytes and SHA-256
for eight prior documents. Text snapshots use `.md.txt` so their original
relative link text can remain byte-for-byte intact without masquerading as
current navigation. Resolve original paths from the repository root and use
the [legacy document map](../../misc/v1/README.md) for relocated files.

- [Former goal](GOAL.v1.md.txt)
- [Former README and classifier results](README.v1.md.txt)
- [Former agent instructions](AGENTS.v1.md.txt)
- [Former alternate agent instructions](AGENT.v1.md.txt)
- [Former North Star](northstar.v1.md.txt)
- [Former corpus goal](corpus-goal.v1.md.txt)
- [Former evidence index](evidence-index.v1.md.txt)
- [Former collaboration contract](COLLABORATION_CONTRACT.v1.json)

These preserve v1 history and its scope-specific authorizations. They are not
active instructions or transferable v2 spend permission. The current
[goal](../../../GOAL.md), [North Star](../../northstar/README.md) and
[incident lessons](../../northstar/V1_LEARNINGS.md) govern the restart.
