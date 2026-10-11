# Explicit owned refresh and failed-build retry

Handler 0.2.2 adds `preview_refresh` after the existing five MCP tools. The local
PreviewSession API gains refresh(). Ordinary poll observes content changes and
skips unchanged input. Explicit refresh reads the current regular bounded ASCII
source and starts a fresh generation even when its digest matches the last
observation. A successful proposal must pass the complete independent byte
comparison before replacing the accepted frame. Closed refresh fails. Repeated
missing/empty refreshes deduplicate the existing observation and never invoke the
builder. Refresh does not alter the source file or extend existing deadlines.

This is a declared reconstruction policy, not recovered native Canvas behavior.
Each accepted proposal uses a fresh owned WASM worker/instance; the finite
renderer is stateless and no user-state migration is supported. Source/module
and allocation hashes identify content; revision/generation identify publication
history. Neither establishes physical native surface identity or reclamation.

The official SDK 2.3.1 used its actual stdio transport against one owned server,
through the established wait-recording supervisor. An unchanged poll returned
identical revision 1/generation 1 status and full frame. An explicit same-source
refresh compiled again and published revision 2/generation 2. An unsupported
ASCII source rejected at generation 3 and retained revision 2. Refreshing the
unchanged rejected source retried the compiler and rejected at generation 4,
again retaining the accepted frame. Restoring supported source and refreshing
published revision 3/generation 5, with historical failure still retained and
current readiness ready. Close cleared availability; a closed refresh returned
a generic isError tool result without exposing compiler details.

Three successful actual CLI waits 0 and two intentional CLI waits 2 all report
drained=true and zero remaining observed processes. The actual server wait is 0;
final owned workers/timers, busy and building are zero. All 18 correlated
responses validate against pinned official JSON-RPC/initialize/tool-list/tool-result
schemas and stay within existing caps. Three fresh compiler stage directories
produce identical source/module/allocation digests for the supported source.
Six consumer full allocations compare independently, totaling 98,304 bytes
including row padding and unused tails. Three fresh V8 instances render the saved
modules against the finite Python expectation. Four resealed faults reject wrong
refresh revision, generation, server wait and a padding byte propagated through
retained packets, allocation hashes, status descriptors and wire/partial records.

A separate owned API control demonstrates unavailable/empty refresh deduplication
without a builder invocation, concurrent refresh rejection, cooperative in-flight
builder abortion on close, and closed refresh rejection. It replays twice in
fresh Node processes. That cooperative fake builder control is not a native
compiler timeout measurement. The actual native compiler controls above are
separately retained. The SDK's 1,108 installed files were rechecked before and
after reuse. The isolated candidate archive passes 95 Python and seven Rust tests.
No unplanned experiment failure occurred; both expected rejection records remain
sealed. Runtime/source, owned transport and native Canvas claims remain distinct.

Evidence: `research/evidence/mcp-refresh-2026-10-11/manifest.json`, SHA-256
`79e1fd30e48ce7473dec5fc3b14c2a88ce3fba119610d372f7629d7de1efbef2`.

Native R1/R2 acceptance, native Canvas state preservation/reset and transport,
browser/Windows/platform delivery and both milestone contracts remain open.
The retained approved capture bridge remains offline/unresponsive; no restart,
permission bypass or user workspace action occurred. The next useful owned work
is an explicit demanded consumer binding that correctly distinguishes current
readiness, retained frame identity and refresh/retry. Native state claims need
independent interaction and correlated lifecycle evidence after bridge restoration.
