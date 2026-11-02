# Native in-flight cancellation and concurrency controls

Static expansion remains paused. These are executed shipped PreviewsFoundationHost controls in isolated owned processes, not replay or a model.

## Demonstrated

- A background native invalidation enters a deliberately blocked observer callback. Cancel on the main thread returns while that callback is still blocked. Weak context remains alive and its owned FD remains open. Releasing the callback permits context deinit/FD close before invalidation returns. Assertions and thread IDs establish ordering. Cancellation is therefore not an in-flight callback drain in this pinned control.
- 100 fresh observer/handle/token rounds run two cancels and two invalidations from gated concurrent GCD jobs. Trace IDs and overlapping begin/end intervals prove cross-thread overlap. Each observer is invoked zero or one times; all owned contexts and descriptors are released after joins. See results.json for this run's counts. Counts are not probability or performance estimates.
- All eight normal controls passed, including the prior six regression cases. The destructor-reentry negative control again terminated its owned child with a matching recursive os_unfair_lock diagnostic. That limitation remains separate from ordinary callback reentry, which passed.

The FD is an owned /dev/null sentinel, not a native transport/render resource. Log serialization and semaphores intentionally perturb scheduling. Sampled interleavings are not proof of race freedom. Scope is the pinned arm64 framework UUID and SHA checked by the executable/runner; handle fixture explicitly selects softAssertDebugOnly. No full target or standalone WASM acceptance follows.

## Reproduce

`python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-runtime-new`

Use a new directory. Optional `--include-negative-control` intentionally terminates only its owned child. Compiler bounds are thirty seconds; native process bounds eight seconds; exclusive controller locking and owned-process-group cleanup apply. No user Xcode process is touched by these component controls.

`native-*.stdout` contains JSONL traces; result files contain actual PIDs/codes/deadlines. `receipt.json` records sources used for execution. `execution-verifier.json (encoded original source)` matches its verifier hash; the final `verify.py` additionally checks distinct callback/cancel threads and actual cross-thread API overlap against those same recorded traces. Native source is unchanged between execution and final verification. Sanitized crash summary matches the negative PID. No Apple instruction text, binaries or raw dumps are published.

Still unknown: internal build notifications, exact private preview-update execution, arbitrary races, all transport/render cleanup and cross-platform WASM parity. Earlier native UI edit/error/recovery observations remain in the prior runtime-validation evidence; they were not rerun here.
