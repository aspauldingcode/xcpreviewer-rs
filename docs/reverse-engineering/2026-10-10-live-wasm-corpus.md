# Persistent host versus the anchored native extent corpus

The persistent WASM host now consumes 84 frozen source-derived revisions in one
owned process. A preparer checks the external source-CLI and native manifest
anchors, then checks every referenced artifact size/hash, source receipt/config,
module receipt and independent full-allocation prediction before copying fixtures.
The corpus preserves the 40 native jobs × two repeats, plus two transparent
independent-only jobs × two repeats. Content-addressed identical payloads are
stored once; separate native/source origins and denominator remain in the index.

Actual macOS ARM64 V8 commits 84 distinct sequential revisions and verifies each
live retained instance. Every 16384-byte allocation matches the independent
prediction (1,376,256 bytes). Eighty also match the externally pinned public
native callback-target allocations (1,310,720 bytes, including 1536 padding bytes
and 1,035,264 unused-tail bytes). These are reused native captures, not new native
Canvas measurements. No compiler runs during replay: each module is tied to its
previous frozen source build and exact source hash.

Three success-shaped proposals with one-bit expected pixel, padding or final-tail
faults reject without changing the current revision/token/frame; subsequent live
instance reads match all retained bytes. All accepted/rejected proposals leave
exactly one owned worker until final close, which reports zero. Two additional
retained controls change a module byte or select a mismatched native reference;
both reject before any frame publication. Two bounded tests pass. A separate
process rechecks every output byte against the independent predictor/native input
and verifies the final worker inventory and sealed artifact hashes.

Evidence: `research/evidence/live-wasm-corpus-2026-10-10/manifest.json`.
Implementation: `tools/re/reloop/livecorpus.py` and `live_wasm_corpus.js`.
The source-build run anchor is
`c7d706c527ec6af1fd22709effc05e5a665edfdb28acc33973586cd764e7c834`;
the independent native run anchor is
`5786fc404ec0181161d42e431b303425260af6adb3d517bf92351cbf542301fa`.
This supports an owned persistent reconstruction policy for the bounded subset;
it does not recover native Canvas transport/hot-reload sequencing, state migration,
native exported PNG fidelity or general SwiftUI. Native UI/private bridge
prerequisites remain unchanged; no Xcode workspace was opened. Scientific review,
graph execution binding and both milestone acceptance contracts remain open.
Next: bind this bounded replay adapter into the reviewed graph and connect fresh
source edits/build results to proposals with stale-build/failure controls.
