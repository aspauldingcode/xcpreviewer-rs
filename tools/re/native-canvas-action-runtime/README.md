# Native failure-action callback and capture lifetime controls

Run from repository root with a new output directory:

```sh
python3 tools/re/native-canvas-action-runtime/run.py --output /private/tmp/canvas-action-fresh
```

Four owned-process controls cover unfulfilled/fulfilled owner destruction on the main thread and a worker thread. The existing failure-mode test case's associated type was minimally qualified as `(action: @Sendable () -> ())`, size 16, using its existing field descriptor and runtime type resolver. A real compiler-created capturing Swift closure is initialized into the known consuming enum-argument slot; no fake function/context pointer is supplied.

Probe has checked Sendable conformance with immutable fields. The worker uses a lock-protected single-consumption native reference lease; the main thread waits for completion before weak/FD checks. The only unchecked Sendable type is that internally locked lease. This is synchronous native ABI/GCD interop, not a Swift concurrency migration or a claim that the whole inherited harness builds in strict Swift 6 mode.

On unfulfilled release, the failure action ran synchronously on the releasing thread while both owned FDs remained open; observer callback did not run. On fulfilled release, observer callback ran during invalidate and failure action was skipped. Captured action context remained alive after fulfillment until owner destruction, then cleared. Returning controls check weak references, deinit/close events and fcntl EBADF. Exact relative destruction order of the two contexts is not generalized.

Existing image hash, loaded UUID/path, metadata and function offsets are pinned. Native execution holds the exclusive controller lock. Compiler stages have 30-second bounds and owned native processes eight-second bounds, with owned process-group timeout cleanup. No user Xcode/simulator/project is accessed. See [exact executed evidence and limitations](../../../research/evidence/canvas-runtime-action-policy-2026-11-02/README.md).
