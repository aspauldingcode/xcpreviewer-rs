# Fresh source builds and stale-result rejection

Three fresh builds of the bounded primary-layer source subset were executed with
the externally verified frozen CLI and unchanged pinned compiler/linker/Node
identities. All three produced modules byte-identical to their pinned source
corpus modules, and all 49152 independent allocation bytes match their native
reference allocations. Unsupported `Text` produced the expected build error.
Compiler execution remains a separate adapter; the source-generation host accepts
completed build records rather than implementing a file watcher or compiler.

The new source host issues immutable generation/source-hash tickets, checks build
source and module receipt consistency, and rejects stale or foreign tickets.
The persistent WASM host checks a synchronous latest-generation guard immediately
before atomic publication and stores source provenance in the same active object
as instance/frame identity. Snapshot provenance is copied. These consistency
checks do not authenticate an arbitrary external build producer.

The actual-runtime control schedules completed fresh-build results out of order:
source A publishes, B becomes stale when C is requested, and C's in-flight prepared
candidate is superseded by an unsupported-source request. Both reject while A's
exact instance/frame/provenance remain live. A subsequent C request recovers and
A then reverses the frame. Three revisions correspond to six source generations.
Five controls cover stale completed results, foreign tickets, source/module
receipt mismatches and in-flight supersession. Final close leaves zero workers.
One bounded source-control test and two prior host/cancellation tests pass.

Evidence: `research/evidence/source-revision-2026-10-10/manifest.json`.
Implementation: `tools/re/reloop/source_revision_host.js` and the persistent
host's publication guard/provenance extension. This is an owned reconstruction
policy tested with actual fresh builds; source-build arrival order is deliberately
scheduled by the control. It does not recover Xcode sequencing, SwiftUI state
migration or native Canvas transport. No Xcode workspace was opened. Scientific
review and graph execution binding remain pending; both milestones stay open.
Next: freeze and bind the combined corpus/source controls into the reviewed graph,
then provide a bounded source watcher with independent build-failure controls.
