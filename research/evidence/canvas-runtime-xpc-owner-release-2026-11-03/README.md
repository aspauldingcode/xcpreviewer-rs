# Native SDK caller-reference release during active callbacks

Static expansion remains paused. This extends the already qualified public-SDK cancellation harness with two caller-reference controls, using the same known native APIs and pinned libxpc UUID. No new function discovery, private ABI construction, Xcode/simulator/project/UI access or protection/signature change occurs. The anonymous listener/client and original marker messages remain in a single owned process with an explicitly configured serial queue.

## What actually runs

Two fresh cohorts each execute five native controls. The previous normal, cancel-inflight and cancel-pending cases provide three regressions. New release-inflight and release-pending cases reach the blocked dictionary/error callback respectively, request cancellation at the established point, then call xpc_release on the caller's explicit client reference and clear that local pointer. The probe makes no further client API call through that released reference; final cleanup skips a second release.

In all four new native case executions, release returns **while the callback remains blocked**, with zero owned capture deallocations and its FD open. The dictionary marker or expected invalid-error reply remains valid after unblock, and the captured object/FD remains live through the final callback-body marker. Its actual dealloc closes the same owned FD successfully; later fcntl observes closure. One captured-object deinit and one reply callback are recorded per child through the further 100ms quiet window.

The caller's explicit reference has been balanced; **connection-object destruction is not measured**. Internal SDK references, peer aliases and exact retain counts remain unknown. A call to xpc_release or its return is not used as a deallocation witness. The measured cleanup concerns the original captured object and its FD, not provider/renderer/port/IOSurface/global settlement.

The invalid connection event is also observed in all qualified cases. The C probe records its observation after caller release without forcing that event to be present in release-mode runtime assertions; the recorded-evidence reader requires the actually captured one-event outcome. The dictionary release case receives its invalid event after its active callback's final marker. Pending-error ordering remains scoped to the observed event constraints. A later peer reply in the pending cases produces no second callback within the bounded quiet window; no indefinite guarantee follows.

## Reproduction and evidence checks

Run the canonical run.py to compile and execute all five modes. The second cohort uses the updated runner that invokes verify.py with --owner-release and requires five results, preventing omission of the new controls. The first cohort's original runner required native child success only; the full five-mode reader was then applied to those original records. Exact executed runner/probe sources are preserved. Both cohorts use identical native probe source. Original streamed events equal their final trace copies before time-origin normalization.

All ten native children exit zero without crash or timeout. Compiler stages are bounded to 30 seconds, child processes to eight seconds with an internal six-second alarm, and callback waits are independently bounded. Native execution holds the exclusive controller lock; it is independently available afterwards. The existing accepted-peer PID checks pass. The anonymous client's server-PID query remains zero and is not upgraded to verified remote identity. The two earlier identity-assertion aborts remain in the predecessor evidence and were not rerun.

Eight synthetic owner-release evidence faults reject, covering premature deinit/FD closure, missing release flag, release ordering/thread identity, reply validity and final FD cleanup. Eight historical three-mode SDK faults also reject with the updated reader. Streamed and final representations are changed together for semantic mutations. These are artifact-reader controls, not new native failure injections. No SDK guard failure or native crash occurred in this checkpoint.

## Scope and acceptance

This is actual **public-SDK native component execution**. Existing static reconstruction supplies context only; no source replay is accepted as native proof. The original diagnostic harness works on the pinned host. Same-process SDK callbacks do not establish private Canvas connection/Swift capture teardown, cross-process cancellation, rendered/state completion or standalone WASM functionality. The test reads a final body marker and a separate dealloc event; it does not claim a general callback-drain barrier or physical heap reclamation.

Only original source, sanitized structured observations, metadata and hashes are published. No Apple binary/private dump is included. No user Xcode/simulator process or PreviewLab project/source was accessed. Native full acceptance remains 0/9; tracked milestone delivery remains 1/26 (3.8%).
