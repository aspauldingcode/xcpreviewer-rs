# Frozen native export admission

This research consumer separates native response normalization from frozen content admission. It rejects the actual cancellation, conflicting structured/text representations, duplicate JSON keys, nonfinite constants, malformed optional metadata, invalid flags and paths. Normalization returns a snapshot path with content acceptance false and never opens that path.

Frozen admission binds the separately sealed expected native path and PNG hash, decodes those same bytes internally, then checks the owned sentinel's color expectations. The earlier design allowed a separate caller-supplied RGBA buffer; that failed proposal remains retained. Four independent parser counterexamples and the original test-coverage gap are also retained.

Eleven tests pass independently and under optimized Python. Encoded PNG negatives exercise altered alpha, uniform frames and wrong dimensions beyond hash identity. `python3 replay.py` verifies the local input hashes and retains one native failure plus two narrowly admitted frozen color samples. This is not a successful native A–B–A sequence or a new native run. The replay and optimized run were checked by the producer after independent core review.

The caller must independently verify the expected mapping's seal. Bundle hashes are not server attestation. Live identity, source/request provenance, glyph rasterization, state, input, transport and portable conformance remain separate obligations. No production/controller integration is made. The copied pixel module is used through its `check` function; its prior standalone entry point is not this bundle's replay command.
