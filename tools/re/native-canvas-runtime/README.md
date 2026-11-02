# Native observer runtime tests

Execute shipped PreviewsFoundationHost, not a model. See [runtime evidence](../../../research/evidence/canvas-runtime-validation-2026-11-02/README.md) for scope and failures.

Run from repository root: `python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-fresh`

Add `--include-negative-control` to intentionally exercise destructor reentry termination in an owned child. Output must be a new directory. No user Xcode process is injected or terminated by these component tests.

The earlier eight-control suite introduced: in-flight cancellation and 100 four-operation concurrent rounds supplement the original six. See [concurrency traces](../../../research/evidence/canvas-runtime-concurrency-2026-11-02/README.md). Cancel returning does not imply that an already active callback has finished.

The earlier default suite included eleven normal controls. Three dispatch controls exercise cancellation of a later observer from an earlier callback, synchronous late registration inside a callback, and cancellation of an admitted later observer while the first callback is blocked on another thread. Cancellation in these dispatch controls did not suppress the later callback. See [dispatch evidence](../../../research/evidence/canvas-runtime-dispatch-2026-11-02/README.md). Callback admission, cancellation return and callback completion are distinct observations. Owned probe FD cleanup does not establish transport/render-resource cleanup.

The thirteen-control suite added self-token coverage. New self-drop/self-cancel-drop controls destroy an executing observer's own token, with/without repeated cancellation, without recovering a strong Probe local in that callback. Context/owned FD remain live through the final callback marker, then clear before invalidate returns; second invalidation does not repeat the callback. See [self-token evidence and reader-coverage correction](../../../research/evidence/canvas-runtime-self-token-2026-11-02/README.md). The runner requires every executed mode to appear in the reader result.

The default suite now includes fifteen normal controls. During native invalidation, an owned observer context deinit can reenter invalidate on its still-owned handle, or synchronously register a late observer that returns without a token. Both new paths returned and cleaned up owned context/FD sentinels. This does not generalize historical cancel-time destructor reentry failure or verify Apple Canvas destruction/resources. See [invalidation-time destructor evidence](../../../research/evidence/canvas-runtime-invalidate-destructor-2026-11-02/README.md).
