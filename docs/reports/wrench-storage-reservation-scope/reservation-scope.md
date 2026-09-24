# Active reservation inventory scope

## Change

The storage checker carries each active reservation's inventory scope into
later status and reserve scans. New records separate required roots from
optional cache candidates. An explicit root remains required even when it
matches a standard cache location. A present recorded root is included; a
missing required root or an unscannable root blocks admission. Standard
optional cache candidates can remain absent. Legacy v1 records have only the
flattened list, so only missing paths matching current standard optional cache
candidates are omitted. Reservation records with malformed IDs or root lists,
a filename/job ID mismatch, or duplicate job IDs block admission instead of
being silently omitted or overwritten in memory.

Focused regression tests cover carried-forward roots, missing and unscannable
roots, legacy optional caches, explicit roots that match cache locations,
persisted scope fields, filename identity, and duplicate IDs. The focused suite
passed 27/27 with Python 3.13's standard `unittest` runner. Pytest was not
installed in the available Python 3.13 or Python 3.11 interpreters. Independent
read-only review passed after repairs for partial new-scope metadata and
persisted optional-cache changes.

Before the final successful run, global storage status was `WITHIN_LIMIT`:
actual 10,043,643,523 bytes, active reservations 36,103,000 bytes, projected
10,079,746,523 bytes. The inventory included a 9,379,396,658-byte UV cache
root recorded by an active job. The local test reservation was 5,000,000 bytes.
Other jobs' reservations were preserved.

This is a checker correctness repair. It does not establish disk-health,
operating-system quota, physical-volume headroom, or enforcement of writes
outside the configured inventory.
