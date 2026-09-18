# Phase 14: strict model-output parser

This phase closes the text-to-verifier boundary. `execute_model_output` accepts
only a JSON object encoded with no surrounding prose or markdown, then routes
the parsed proposal through the existing schema and action verifier. Empty,
malformed, non-object, or decorated responses abstain with stable fallback
reasons.

This prevents a model response from gaining authority through heuristic JSON
extraction. The tests include the exact Qwen output shape from Phase 10 plus
markdown, prose, array, and malformed-JSON rejections.
