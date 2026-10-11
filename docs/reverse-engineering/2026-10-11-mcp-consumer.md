# Correlating an owned SDK consumer snapshot

The scoped JavaScript PreviewConsumer accepts the already measured official SDK
callTool boundary. It samples status, typed frame and status again. Both statuses
must match and the decoded frame descriptor must match that status; otherwise it
retries once. Two attempts exhaust after at most six tool requests. SDK request
options retain the 5s timeout; arbitrary providers that ignore those options are
outside this bound. It recomputes readiness, validates the typed allocation,
rejects revision/generation rollback and changed identity for an existing
publication, and retains the prior accepted snapshot on failure. Returned status,
descriptor and allocation copies are detached. Concurrent sample calls reject.
An accepted closed snapshot is terminal for this consumer and clears its frame.

This helper serves the existing owned MCP workflow, not a broad language binding
or native Canvas protocol. It establishes coherent matching observed replies,
not perpetual freshness after sampling or an atomic server transaction. A new
server session requires a new consumer. The finite model does not migrate user
state, establish native transport ordering or provide browser/platform acceptance.

An actual official SDK 2.3.1 control deliberately publishes a second supported
source between the consumer's first status and frame requests. The first status
is revision 1 (13×7); the frame and second status are revision 2 (11×6). Those
individually valid replies contradict the claim that separate tool results always
represent one publication. The consumer retries exactly once and accepts the
matching revision 2 bracket. Repeated unchanged snapshots remain identical. A
caller mutation of a returned allocation/status leaves the internal accepted
snapshot unchanged. A later unsupported refresh retains revision 2 with stale
readiness; closure produces an unavailable frame and terminal closed status.

One actual server wait is 0. Two successful fresh compiler waits 0 and one expected
unsupported wait 2 report drained=true and zero remaining observed processes.
Final workers/timers, building and busy are zero. All 27 correlated responses
validate against pinned official schemas. Five wire allocations (81,920 bytes)
and four saved consumer allocations (65,536 bytes) compare against independent
finite Python expectations, including padding and unused tails: 147,456 relevant
bytes total. Two fresh V8 instances independently render saved modules. Module,
source, toolchain and actual wait receipts correlate with the sealed transcript.
The SDK's 1,108 installed files were rechecked before and after reuse.

A separate fresh-process control rejects eight hostile histories while retaining
revision 2: publication rollback, generation rollback, same-publication identity
change, two exhausted race brackets, inconsistent availability, invalid allocation
hash, false readiness and isError tool failure. It verifies concurrency rejection
and detached copies. It replays twice. Four resealed evidence faults reject a
wrong consumer snapshot, erased race, nonzero wait and a padded row byte changed
consistently across frames, allocation hashes, status descriptors, snapshots and
wire/partial records. The isolated candidate passes 97 Python and seven Rust tests.

Failures remain retained. The first recorder held a caller-owned status reference;
the intentional caller mutation changed the saved status width while its frame
remained correct. Actual wire replies and consumer internal copies were correct,
but wait0 did not make that record coherent. Copying status/descriptor at the
recording boundary fixes this recording defect. The corrected larger control
then hit the existing 10s channel deadline during a later recovery refresh. Its
SDK control exited1 although the server waited0 and cleaned all workers/timers.
It has no completed result.json and is not accepted as completed workflow evidence.
The final control removes that separately completed recovery workload; deadlines
and byte caps remain unchanged. Compact failed records and external manifest
anchors are published, with complete owned failed artifacts retained locally.
Recovery remains scoped by the prior anchored refresh control.

Evidence: `research/evidence/mcp-consumer-2026-10-11/manifest.json`, SHA-256
`c98b1cbd2028475f66f988e82f637a8ab1837f641e72965ab30fea7784142bad`.

The approved private Xcode bridge remains offline/unresponsive, without restart
or permission bypass. Native R1/R2, correlated Canvas lifecycle/state/transport,
actual browser/Windows delivery and both milestones remain open. Next: prove a
server-side atomic sample or declare the bracketed-observation contract for the
actual demanded canvas consumer, and falsify terminal/malformed peer boundaries
before broader binding delivery. Independently restore native capture prerequisites.
