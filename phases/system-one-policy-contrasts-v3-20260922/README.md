# Corrected Wrench policy contrasts

This authored training set contains 806 unique requests from 40 contrast
groups, with 359 Wrench-eligible and 447 abstain labels. It was built from
Wrench's action and bounds contract using 12 tracked files outside the frozen
5,600-case suite's path inventory. It has zero exact prompt overlap with that
suite. Its [audit](audit.json) checks tracked files, positive byte caps, and
positive line ranges against the actual checkout.

The cases are training material, not a test or captured real workflow data.
The 5,600-case suite stays out of fitting and calibration. Human review of the
authored labels remains pending.
