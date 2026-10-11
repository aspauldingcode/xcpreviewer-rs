# Shared-event carrier discriminator

An owned `MTLSharedEventHandle` cannot be archived into ordinary secure `NSData` in this measured environment: both baseline and corrected executions return no data and `NSCocoaErrorDomain` code 4866. An ordinary secure string archives and decodes successfully. The same event handle instead passes through a typed public anonymous `NSXPCConnection`, reconstructs an event with value 3, and signals value 7 to release the sender's gated Metal command. This is a same-process Foundation XPC control, not an independently executed receiving process or a Canvas wire observation.

## Selection and predictions

The graph has no unfinished running or reconciliation wake. Live capture remains blocked because the retained approved private bridge is offline; no restart or workspace is opened. R3 requires synchronization evidence, while R2 requires resource reuse/completion boundaries. Parent two-queue seal `0841c787c1afff6c0da6833cb5dd78dd5f82ed02c2669e948ae09a71109c615c` establishes local event ordering. The missing carrier boundary is more discriminating than another malformed owned JavaScript packet.

The installed public Metal SDK declares `MTLSharedEventHandle` as `NSSecureCoding` and describes passing handles through XPC. The experiment tests the tempting stronger inference that ordinary byte archiving suffices. The archive error falsifies that inference for this fixture, without proving that every archival API or carrier must fail. It does not attempt to encode/decode Mach attachments into an ordinary pipe, publish handle bytes, or infer a private Apple transport format. No encoded handle data was produced or retained.

## Controls and execution

Each helper owns a new public Metal event at value 3 and its shared-event handle. Secure handle archiving uses `NSKeyedArchiver` requiring secure coding and records sanitized error domain/code and data availability. A separately known string uses the same archive API and a typed secure unarchiver; exact decoded text is required. Exception names are captured without dumping arbitrary exception details.

A public anonymous `NSXPCListener` accepts one owned client endpoint in the same helper. Its typed interface receives `MTLSharedEventHandle`, reconstructs with the device's `newSharedEventWithHandle:`, records value 3, creates an independent event and signals that event to 99, and confirms the imported event remains 3. The imported event then signals 7. Reply PID must equal the sender/helper PID: this explicitly rejects a cross-process claim. There is no audit-token peer authentication claim; cross-process endpoint transfer and ownership remain next work.

Before the RPC, a default command waits for event 7 and fills 44 active bytes in each of six rows at stride 256 with `0x77`. The entire 16-KiB destination begins as `0x5c`. A bounded 20ms semaphore wait times out with zero callbacks and value 3. The XPC reply arrives within three seconds and the original sender event observes 7. The helper always explicitly sets its owned event to 7 after the RPC attempt, including failure, so a failed carrier does not leave its GPU command waiting. Completion then requires one callback, status 4 and a full copied allocation within five seconds. The reader requires the value 7 observation before fallback; fallback alone cannot satisfy carrier acceptance. No CPU data is read while queued work is pending. Connection and listener are explicitly invalidated.

Compile and subprocess deadlines are 15 seconds; helper alarm is 12 seconds. Four native helpers exit zero, two baseline and two corrected; neither deadline nor input is enlarged. The baseline's archive-success assumption is contradicted and its instrumentation cannot receive acceptance: pending callback count was not atomic and two predicates serialized as integers. Its source/results/waits and false assessment remain under `baseline/`. The corrected observer uses an atomic callback counter and explicit Boolean boxing. The baseline remains descriptive corroboration only, not an accepted concurrency proof.

## Evidence and verification

Environment: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64, Apple M1 unified memory. REA 6.2.0 independently binds owned baseline artifact `51c3350e95faf7849e4bc53ec9634dafa5ccf69a24c56122f39e571a3d56eba0` (`ev_74fdd7a1d09d84d0015cea6e5ef22e14fd1bf63cd1f6b99714447f3c301fd6d7`) and corrected artifact `1726c02f5d8d6a61214c68d334928f02598931ca520cbf66da3a008924bc09b8` (`ev_d4218d902f9a9f288fe5288552072029e3f58ae38c17bf22af0c510117068791`). Both target sessions close. Static artifact provenance is separate from actual subprocess measurements; owned executables remain local.

Independent prediction checks 131,072 saved bytes across both retained baseline and corrected runs: entire initialization and completion allocations, including row padding and allocation tail. Only corrected runs satisfy the scoped acceptance predicates. Seven resealed mutations change actual wait, archive outcome, peer PID, independent-event isolation, completion status, row-padding byte 44 and tail byte 16383; each must fail despite recomputed hashes. The source and frozen corrected helper must match. Isolated candidate checks also verify the anchored two-queue parent evidence.

Evidence directory: `research/evidence/gpu-event-carrier-2026-10-11`; manifest SHA-256 `7a56105dcb8c3775a44305aeac80cc4b157230e3238499d0f6613f9faadb7bef`. Reader: `tools/re/tests/verify_gpu_event_carrier.py`.

## Remaining work

Ordinary byte archive failure and same-process public XPC handle reconstruction are scoped observations. They do not establish cross-process GPU signaling, received Mach right accounting, final physical reclamation, automatic timeout cancellation, discrete GPU behavior, private Canvas envelope or lifecycle policy. R2/R3, native capture and both milestones remain open.

Next implement an owned independently executed receiving process with a public XPC endpoint/handle carrier and verified identity/cleanup. Do not retry the unchanged ordinary archive failure or claim an anonymous listener endpoint can itself be transferred through ordinary secure bytes. Preserve explicit fallback release and bounded waits. Approved bridge restoration remains a separate external prerequisite.
