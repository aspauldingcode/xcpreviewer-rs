# Native SDK cancellation while a reply callback is active

Static expansion remains paused. Work switches from the unchanged Swift file-removal failures to an existing recovered transport/cancellation boundary. The [earlier SDK cancellation evidence](../sdk-cancel-reply-2026-10-24/README.md) connects recovered private source calls to public libxpc operations and explicitly leaves private connection invocation unqualified. This experiment executes those public SDK operations with original owned endpoints/messages. No new private source body is recovered or reverified, and no private Canvas connection, Xcode process, simulator or project is accessed.

## What actually executes

Each native child creates an anonymous listener, endpoint, client and accepted peer in the **same owned process**, and explicitly configures a serial target/reply queue. The message marker is original fixture data, not a Canvas wire envelope. The reply block captures one original Objective-C object that opens an owned FD and closes it in dealloc. Its caller releases its reference after submission. Thread/monotonic/sequence events stream as they occur and are independently compared to the final recorded trace.

Two fresh qualified cohorts each pass three controls:

* Normal: an actual dictionary reply enters a blocked callback. The captured object/FD remains live, the marker remains valid when unblocked, and deinit/close follows the final callback marker. Cancel afterwards produces a separate connection-invalid event.
* Cancel-inflight: main requests cancellation while the dictionary callback is blocked. Cancel returns while capture-drop count remains zero and its FD open. After unblock, the existing dictionary/marker is still valid. The owned capture deinitializes/closes afterwards. Cancellation return is not completion of that already active callback in these controls.
* Cancel-pending: the peer retains an unsent reply while the client cancels. The actual reply callback receives XPC_ERROR_CONNECTION_INVALID; its owned context/FD remains live while that error callback is blocked and closes after its final body marker. A later peer reply is submitted. One reply callback is observed through the further 100ms quiet window; no indefinite exactly-once or no-future-callback guarantee is inferred.

All six controls observe one capture destruction, successful close, checked FD closure and zero configured-queue mismatches. The error-reply callback and connection-invalid event are separately observed. The reader preserves causal constraints without freezing their general relative ordering in the pending-cancel case. Callback-returning is an explicit end-of-body marker; capture destruction is separately observed afterwards, not inferred merely from cancel or process exit.

These are native public-SDK component controls, not cross-process transport, private Swift capture-layout qualification or native Canvas resource settlement. They measure one owned captured object/FD. Listener/queue/Mach-port/IOSurface/renderer/provider/global reclamation and private callback ownership remain unverified.

## Identity qualification failures retained

The loaded cancel operation resolves to /usr/lib/system/libxpc.dylib UUID c40fcae87a173d8287cb3da4802adef1. Each accepted peer's PID equals the helper PID. All six qualified client-side server-PID queries return zero; that query is recorded as unavailable identity in this setup. The listener was constructed by this helper through an unpublished anonymous endpoint, rather than connecting to a named external service. This does not establish arbitrary service audit identity.

An earlier added guard incorrectly asserted the client's server-PID query equaled the helper PID. The normal mode aborted with SIGABRT in two owned processes. The second planned run executed because the shell batch did not short-circuit after the first failure; this was an avoidable harness mistake. Both original sources, process outcomes and assertion diagnostics are retained. No third unchanged attempt occurred. Failed numeric query values were not logged, so zero is not retroactively assigned to those attempts; object/FD cleanup there is unknown. Raw crash material remains local.

The changed probe records the query and checks the accepted peer instead of asserting unsupported client identity. It also flushes structured events immediately, avoiding the failed attempts' empty buffered trace. Two subsequently qualified cohorts pass with the new code. Earlier successful exploratory controls remain local; claims here use the two published complete cohorts. No user process was terminated or protection/signature changed.

## Verification and evidence scope

Compiler stages are bounded to 30 seconds; native children have a six-second alarm and eight-second controller deadline. The exclusive controller lock covers runtime execution and is independently available afterwards. Six qualified children exit zero without timeout; the two earlier identity-guard aborts remain distinct qualification failures, not expected passing failure controls. The expected invalid reply in cancel-pending is actual native error delivery.

Eight synthetic semantic evidence faults reject. They alter both streamed and final trace copies, so rejection exercises ownership/order/error/identity assertions rather than just duplicate-record mismatch. These faults are reader tests, not native failure injections. A reader pass cannot upgrade a private Canvas or renderer contract.

Native runtime verification covers actual SDK deliveries, cancellation, callback/capture ordering and owned FD close. Existing static reconstruction provides context only. Simulated replay supplies no primary native proof; the synthetic corruption checks test evidence validation. Working functionality is an original diagnostic harness on this pinned host. No product Rust/WASM behavior changes or tests are claimed.

Only original code, sanitized structured observations, metadata and selected owned assertion diagnostics are published; binaries, raw Apple dumps and crash files stay local. Normalized time origins preserve ordering. Full native areas remain 0/9; milestone delivery remains 1/26 (3.8%).
