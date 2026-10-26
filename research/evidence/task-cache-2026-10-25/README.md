# Serialized task-cache storage and destination failure policy

Recovered PreviewsFoundationHost.AsyncThrowingCache actor initialization, value
state machine/resume paths, task closure and invalidate body plus folded default
argument stubs, and Pipeline DestinationCapabilitiesCache initializer.2,356 source
bytes independently match Mach-O/LLVM. Named default aliases disambiguate folded
stubs. Reflection includes $defaultActor,clearOnFailure,storage. Actor storage is
Dictionary<Key,Task<Value,Error>>. Exact dictionary get/set, Task.value/cancel,
actor initialize and task allocation/switch bindings are resolved where asserted.
The selected framework has no Modules entries; no private actor import or guessed
Swift ABI invocation attempted. Source analysis remains useful without that route.

A hit returns/awaits the stored task. A miss creates/stores a task before awaiting.
Generic clearOnFailure defaults false. Only the creating lookup's error path
conditionally assigns nil to storage[key]; reused waiter errors simply propagate.
No task-identity comparison guards cleanup. After invalidation/refetch, a late
creator error may remove the replacement under the same key. Success does not
remove the handle. Invalidate defaults cancelingTask=true: look up/request cancel
when present, then remove the entry. False removes without cancellation. Removal
and cancel request do not establish completion, waiter release or settlement.

Pipeline constructs all three destination capability caches with explicit true,
including ContentOverrideKey -> Optional<ContentOverride> in the middle slot.
The typed content_override_task_cache factory therefore uses clearOnFailure=true;
the generic TaskCache and trace defaults remain false. Exact metadata reference,
true instruction and constructor binding are asserted. No claim that generic
error-retention default is the destination-specific policy.

Original TaskCache stores host-owned cloneable handles. acquire runs a provided
factory only on miss; TaskAcquisition captures key/handle/created status. A consumed
observe_failure ticket clears only on creating lookup + enabled policy, without
a generation guard. invalidate requests cancellation through a host callback
before removal. Caller tickets/returned handles survive entry removal. Observe
failure only on the cache that produced the ticket. Hosts own executor creation,
actual async task results/awaiting, synchronization, cancellation cooperation and
handle lifetime. This is not a Rust async executor, Swift Actor, native task value
cache or scheduler model. The late-failure trace is source-guided, not a reproduced
private actor race. No native executor timing or global resource parity claimed.

The bounded task-cache inspector uses original operations/acquisition-ticket IDs
and synthetic task handles keyed by existing content-override request identity.
It validates the full trace before execution, rejects future/consumed tickets and
malformed late requests, and returns complete events/start counts/retained handles/
cancel requests. Summary shows eight events. This is not Apple wire serialization.

335 Rust tests,26 original public Swift Dictionary/Foundation state compositions
(20 accepts/six rejects),46 actual WASI invocations (26 canonical+20 summaries),
20 Foundation reparses pass. Complete type-sensitive traces and byte-identical
bounded summaries agree. Three new tests cover factory coalescing, retained failed
handles, creator-only/stale cleanup, destination policy, cancellation directives,
external handle survival/scoped Rc release and full CLI traces. Rust-owned Rc
release is scoped evidence only, not native resource settlement. Native controls
are original serialized Dictionary/Hashable compositions with synthetic handle
IDs; they do not run an actor, Tasks, scheduler or shipped private cache. Disposable
source/focused/composition/WASI replay passes; full335-test output retained.

One exploratory metadata assertion omitted synthesized $defaultActor; corrected
after actual fields were read. A guessed prior symbol-inventory path was missing;
bounded actual nm/demangle inventory succeeded. Failures retained separately from
native behavior/access. Prior Ghidra/import limitations remain in their actual
probe scopes. REA identity matched; closed session/provider binding null; no
Xcode MCP, native UI process action, re-signing or system change. Raw Apple code
and symbols remain ignored/local. Both milestone contracts remain incomplete.

Next: runtime correlation of coalescing/cancel/error behavior where typed access
exists, and full previewRequests mode/associated-group/request construction and
content-override service mapping. Native actor/executor, UI/provider lifecycle,
transport/rendering/refresh and global resource settlement remain open.
