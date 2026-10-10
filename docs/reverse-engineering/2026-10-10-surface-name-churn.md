# Retired Mach names under bounded owned allocation churn

A retired numeric Mach name is not a durable resource identity. Two accepted sealed campaigns each run four BGRA shapes twice, retiring the first IOSurface send right while keeping its CF surface alive. Each execution creates, looks up and deallocates 128 send rights for a distinct second surface. The second campaign observes 15 exact retired-name recurrences, after 13 in the first; on each recurrence the old numeric name resolves the replacement surface ID. Otherwise stale lookup returns null. Every replacement lookup returns the second ID, every live send reference count is one, and every post-deallocation name query returns KERN_INVALID_NAME.

Across both accepted campaigns, 2,048 sequential right lifecycles pass. All 2,048 names share the original numeric name shifted right by eight; this is a measured numeric comparison, not an asserted kernel generation contract. The counts of exact recurrence differ across executions. No deterministic recurrence schedule, arbitrary allocation interleaving or cross-task behavior is claimed.

The two complete campaigns independently compare 786,432 bytes: original producer allocation, replacement producer allocation and final valid replacement-name lookup allocation, for sixteen executions. Each allocation is initialized to 0xa5, including row padding and unused tail, and active BGRA bytes follow a separately implemented Python formula. Positive seed change separates resource contents. Per-churn stale lookups compare resource IDs; they do not snapshot pixels at every recurrence. The helper's `stale_base64` output is the final valid replacement lookup allocation, retained as a field name from the initial rejected forced-rename control.

## Failed controls retained

The initial sandboxed run cannot create IOSurfaces and remains inconclusive. Native execution reaches explicit `mach_port_rename`, but that route returns -303, `(ipc/mig) bad request message ID`. A changed diagnostic records the exact refusal and owned helper exit7. No unsupported kernel bypass is attempted. Switching to bounded actual allocation churn removes the forced-rename assumption.

The first churn run exits successfully but remains inconclusive: Objective-C boxed C comparison values serialized cleanup fields as integer1. The strict verifier rejects these. Explicit BOOL casts correct the producer; both accepted seals use that correction. All six manifests and artifacts verify against published hashes in [sanitized evidence](../../research/evidence/surface-name-churn-2026-10-10.json). Failed native subprocesses release task-local resources when their owned process exits; no success cleanup claim is made for those executions.

## Reconstruction consequence and limits

A consumer must retain an owned resource right for its intended read lifetime, and bind resource use to a session and producer-issued generation where stale requests can persist. Generation policy is proposed reconstruction design, not a recovered Canvas field. Immediate null after name retirement cannot justify caching that raw name indefinitely: this experiment directly demonstrates later aliasing.

R1/R2 and milestone1 remain open. This is one-task public IOSurface/Mach CPU behavior, with no Apple private code invocation, live Canvas wire observation, GPU completion policy or physical memory reclamation proof. No Xcode windows are opened. Five new verifier tests cover missing/type-corrupt evidence, alias identity, cleanup and nonzero exit, active/padding/tail byte faults, and the exact-name recurrence countermodel; all 232 repository tests pass.
