# Peer loss before and after shared-event signal

Both owned peer exits fail the pending public XPC request with `NSCocoaErrorDomain` 4097 and no reply. Exit 47 before the shared-event signal leaves sender event 3 and GPU work pending; exit 48 after the signal leaves sender event 7 despite the failed request. Both sender controls explicitly release their own event and obtain one completed-status-4 callback with exact full bytes. A failed reply does not by itself classify the event dependency or GPU outcome.

## Selection and scope

Parent cross-process seal: `a2fc1388b339af82b3c0d52f5ac0b4f27b350d696ca515c15730a7d484792a89`. That control covers normal peer exit and wrong-event-only signaling. The graph has no unfinished running/reconciliation wake, and separates research from delivery review; both milestones remain incomplete. R1/R2/R3 require failure and completion boundaries. The retained approved private bridge still reports running/responsive false; no restart or owned workspace is attempted. REA availability is separate.

This experiment uses the same finite public shared-event/XPC fixture in a separately executed owned launchd peer. It does not observe private Canvas envelopes, cancellation policy or final physical release.

## Prediction and changed peer

Each parent owns event 3 and a default Metal command waiting for event 7, encoding six 44-byte row fills with `0x77` at stride 256 into a 16-KiB shared buffer initialized entirely to `0x5c`. An initial 20ms wait times out with zero callbacks and event 3. The peer's listener accepts only the runner-owned live parent's public connection processIdentifier. The typed method reconstructs the shared event and signals a separately created event to 99, which leaves the imported event unchanged.

Before mode records imported value 3, accepted parent PID, peer PID and intended exit 47 to the owned job's stdout, then immediately `_exit(47)` without signaling the imported event or replying. After mode changes only the imported signal and intended exit: it signals value 7, records it and `_exit(48)` without reply. The runner retains both deliberately nonzero peer outcomes, rather than treating parent exit0 as complete success.

Both modes invoke the request error handler exactly once, with error4097 and null reply. The parent samples original event value 3 or 7 after that error. Before mode performs another20ms semaphore wait: both actual results are nonzero49, zero callbacks, event3. After mode skips that wait because event7 is already visible. The parent always explicitly signals its own event7 after the RPC attempt, including failure, then requires one callback/status4/full snapshot within five seconds. Event7 visibility after peer loss is measured; the helper does not establish whether the GPU callback had already happened before fallback in after mode. No CPU data is read while work is pending. This is explicit recovery, not automatic cancellation or a claim that transport error stops GPU work.

## Identity, observer and service cleanup

A random temporary `org.xcpreviewer.owned-event-<UUID>` job is registered in gui/503 with the exact compiled owned helper and expected parent PID. There is no LaunchAgents installation or KeepAlive. The parent begins only after bounded registration. Peer stdout belongs to that exact owned job and records the expected accepted parent PID, distinct peer PID, value and exit. The launcher parent PID matches the parent output.

After the peer dies, the parent's public connection processIdentifier is 0 in all four runs. It cannot supply a live peer identity at this boundary and is not repurposed as the prior peer PID. The identity evidence here is the owned job/source-bound journal and the peer's prior public PID acceptance predicate, not a new audit-token/code-signature proof. The journal is a finite helper observation; it does not enumerate imported Mach rights.

The runner observes each exact job's last exit47 or48, no running peer PID and matching executable path. Cleanup unconditionally attempts bootout for its own random name, including uncertain registration outcomes; measured bootout returns0, subsequent print returns113 (service absent), and temporary plist/stdout/stderr files are removed in all four runs. No finish RPC is sent to a dead peer, preventing deliberate service reactivation. No user Xcode/simulator process is killed. General registration-timeout cleanup remains untested; accepted evidence covers these four executions.

Compile/subprocess caps are15 seconds, helper alarm12 seconds, launchctl calls five seconds, RPC three seconds and completion five seconds; four native executions consume the four-experiment cap. Atomic counters and semaphore ordering protect callback/error observations. No deadline is enlarged. Archived runner scripts are exact producer provenance, not replay commands against sealed folders.

## Evidence and verifier

Environment: macOS26.5.1 (25F80), Xcode26.6 (17F113), arm64, Apple M1 unified memory. REA6.2.0 binds owned artifact `2bbce09ec9ff28920051aacfd6a1293022cafdb708e01212d2b874110c3b0b53` (`ev_b35b6391ba8960ceb7c022dd95155f56b53d142693cc05b39a5d02c8ec9eff77`); its target closes. Static artifact provenance is distinct from subprocess/launchd runtime outcomes. Executable and private encoded handles are not published.

Evidence: `research/evidence/gpu-event-failure-2026-10-11`, manifest `103b36861e57935e078de43f8c86473021f00bc5400b6ec7eb26f72ec125ca06`. Independent reader requires four parent waits0, deliberate peer exits47/47/48/48, absent owned services, expected typed error/null reply, source-bound peer journals and before/after signal distinctions. Four initialization/completion pairs compare131,072 independently predicted bytes, including every padding/tail byte. Eleven resealed faults change parent wait, invented reply, error code, accepted-parent journal, premature signal, pending wait, completion status, peer exit, cleanup, padding44 and tail16383; all reject despite recomputed hashes. Current helper equals frozen source. Isolated candidate checks also verify the parent peer control.

## Remaining work

R1/R2/R3 and both milestones remain open. This covers process-loss effect on a retained sender event and explicit fallback, not exact event/Mach right accounting, final physical release, received surface cleanup, automatic recovery, discrete GPU semantics or native Canvas policy.

Next investigate imported event/handle lifetime after disconnect and explicit owner drops, or a demanded independent product gate. Avoid repeating ordinary archive failure or the same peer exit controls. Approved Canvas bridge restoration remains an external prerequisite.
