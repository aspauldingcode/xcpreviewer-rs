# Owned GPU event timeout and explicit recovery

The audited receiving-process Metal readback now has a bounded event-gated timeout control. This adds a GPU-adjacent failure boundary to R1/R3 without claiming that the owned policy is Xcode Canvas policy. Baseline: Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64, Apple M1, shared BGRA8Unorm. The previous peer readback seal was verified against its published anchor before extension.

## Prediction and execution

Before the receiver texture-to-buffer blit, the owned command encodes a wait for shared-event value 1 while its current value is 0. The first completion semaphore deadline is 20 milliseconds. Acceptance requires timeout, zero callbacks, event still 0 and a committed or scheduled command. Callback count/status use C atomics so the pending-state observation has no unsynchronized counter access.

The fixture always explicitly raises the event to 1 before assessing the timeout control. This prevents a negative-control rejection from intentionally leaving an unreleased gate. It then allows at most five seconds for successful late completion, requires exactly one completed callback and no command error, and only then snapshots the destination. The enclosing helper alarm, fifteen-second subprocess deadline and exclusive bounded controller remain active. This is timeout observation followed by explicit recovery, not command cancellation or automatic deadline cleanup.

Independent expected bytes cover producer initialization/render, destination initialization/blit, peer CPU snapshots/mutations, post-exit access and retained-port-only access. Source padding/tail remain `0xa5`; untouched destination padding/tail remain `0x5c`. Four geometries, clean/abrupt peer exits and two repetitions yield 16 helpers and 128 whole-allocation comparisons, totaling 2,097,152 bytes per campaign. Both event-timeout campaigns and the ordinary peer GPU readback regression pass exactly. Existing audited identity, actual exit status and local send-right cleanup checks remain required.

All 32 timeout-control executions observed committed status 2 before release, event 0, no callback and semaphore timeout. After explicit event signal each completed once with exact bytes. Committed status does not prove that hardware reached the event wait; scheduler delay is not separated from gate delay. There is no CPU read of the pending GPU destination.

## Verification and scope

Fault controls reject missing fields, integer substitutions for Boolean flags, callbacks before release, completed status before release, wrong event values and missing/wrong deadlines. Parameter validation requires strict Boolean flags and reviewed consumer/producer configuration. All 142 tests pass. Three seals and sanitized metrics are published in [evidence](../../research/evidence/gpu-event-timeout-2026-10-09.json); local private/raw artifacts remain unpublished.

Apple's [encoded event wait](https://developer.apple.com/documentation/metal/mtlcommandbuffer/encodewaitforevent%28_%3Avalue%3A%29) orders subsequent encoded work behind the event value. The [shared-event signal property](https://developer.apple.com/documentation/metal/mtlsharedevent/signaledvalue) supplies the explicit CPU release used here. These API contracts explain the fixture; observations do not trace GPU instructions or recover Apple's private Canvas synchronization.

R1/R3 stay open for actual Canvas policy, cancellation, unsynchronized overlap, broader formats/storage modes, internal driver resource holders and final physical reclamation. No cross-process event handle is transferred. No Xcode windows opened, user processes terminated or system protections changed.
