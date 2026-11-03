# Native late registration while an earlier callback is blocked

Static expansion remains paused. This extends the existing shipped PreviewsFoundationHost observer harness using already-qualified register/invalidate/token APIs and original owned context/FD sentinels. No new native function recovery, Xcode attachment, project edit or UI action was required. The framework file SHA and loaded image UUID are pinned by the existing runner; each owned native execution holds the shared controller lock and has an eight-second process deadline. Compiler subprocesses are also bounded.

## What the native test actually does

A first observer is registered, its caller-owned context reference is dropped, and a worker invalidates the native handle. The first callback signals entry and waits on a bounded semaphore. While it remains blocked, the original thread calls invalidate again. In both captures this second call returns without waiting for the first callback. Assertions then require the original weak context to remain non-nil and its owned FD to remain open.

That original thread next registers a distinct late observer. Its callback executes synchronously on this registering thread before registration returns; the original callback is still blocked on the worker. Native registration returns no token. Dropping the caller's late-context reference clears that weak reference, executes its deinit and closes its own FD, while the first context is still alive and its FD open. Only then does the harness release the first callback. After the worker finishes, the first weak context is nil and its FD closed. A third invalidation produces no additional callback. The original token is destroyed and handle released after these joins.

The traces show two active callback intervals on distinct threads, not serial delivery through a single callback executor. The second invalidate return is not a completion barrier for the first invocation's callback. This result concerns these native component controls and schedule; it is not a claim about arbitrary observers, all possible interleavings, UI-thread delivery or formal race freedom. Lifetime assertions use owned sentinels, not an inferred target allocation count.

## Reproduction, assertions and failures

Both fresh builds execute all sixteen normal native controls successfully, including the existing one-hundred-round cancellation/invalidation schedule test per run. The first run's original reader was still the fifteen-control version because an editing script assertion prevented its update. The outer runner correctly rejected that omission with `Verifier omitted an executed control` and exit one. This is a harness coverage failure, not an accepted successful suite result. The corrected sixteen-control reader checks both captured runs; the second fresh build/run completes the entire runner with exit zero. Exact original readers, native source, structured traces, process outcomes and corrected results are preserved. No native child crashes or times out. The historical recursive-lock termination control was not rerun.

An artifact-packaging guard initially treated compiler stderr as a native test stderr file; its assertion stopped packaging. The corrected filter keeps compiler outcomes/hashes separately. All sixteen native execution stderr files in each run are empty. Compiled binaries, module caches and private crash material remain local.

Eight synthetic evidence faults reject: dead original context, closed original FD, retained late context, unexpected late token, unclosed final FD, mismatched destructor FD, same-thread callback attribution and callback-before-add ordering. The ordering fault renumbers sequence/timestamps so rejection does not rely on malformed event sequence. These tests validate the reader; they do not inject failures into native execution.

Run `python3 tools/re/native-canvas-runtime/run.py --output NEW_DIRECTORY` on the qualified host. Run the evidence root `verify.py RUN_DIRECTORY` to inspect recorded traces and `mutations.py RUN_DIRECTORY` for synthetic corruption controls. Existing native failures are intentionally excluded unless explicitly requested with the runner's negative-control flag.

## Evidence boundaries

This is **native component execution**, not static reconstruction or simulated replay. The original harness works on this qualified host. It does not verify Xcode EditorScene destruction, weak zeroing after document closure, rendered preview state, transport/render resource release or standalone WASM functionality. Prior positive EditorScene weak-load evidence remains separate. No user Xcode or simulator was accessed or terminated; no project changed; controller independently available afterwards. Full native-area acceptance remains 0/9 and tracked delivery remains 1/26 (3.8%).
