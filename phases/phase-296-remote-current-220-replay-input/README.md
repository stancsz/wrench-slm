# Phase 296: remote current 220 replay input

This phase adds one complete teacher capture to the repository so a fresh
5060Ti worker can pull a self-contained, hash-matched replay input. Earlier
remote attempts could run the package-only diagnostic but had no matching
teacher receipt, so they could not produce a teacher-aligned result.

The bundled teacher receipt is proposal-only evidence. It does not execute
actions, contain credentials, or authorize production use. The current cases
file remains the authority for the 220-row suite and has canonical/raw SHA-256
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.

The remote worker must use a fresh temporary export of the pushed commit,
resolve the v103 NVFP4 package from the approved Hugging Face revision or an
identical local artifact, preserve 10% RAM and VRAM for the host, and run the
package replay with the bundled teacher file. It must return the complete
trace-manifest hash, evaluation hash, source commit, package identity, host
identity, resource snapshot, and every failed attempt. A package-only result
or wrong-host run remains diagnostic and must not be promoted to parity.
