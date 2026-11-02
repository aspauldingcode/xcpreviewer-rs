# Native observer runtime tests

Execute shipped PreviewsFoundationHost, not a model. See [runtime evidence](../../../research/evidence/canvas-runtime-validation-2026-11-02/README.md) for scope and failures.

Run from repository root: `python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-fresh`

Add `--include-negative-control` to intentionally exercise destructor reentry termination in an owned child. Output must be a new directory. No user Xcode process is injected or terminated by these component tests.

The earlier eight-control suite introduced: in-flight cancellation and 100 four-operation concurrent rounds supplement the original six. See [concurrency traces](../../../research/evidence/canvas-runtime-concurrency-2026-11-02/README.md). Cancel returning does not imply that an already active callback has finished.

The default suite now includes eleven normal controls. Three dispatch controls exercise cancellation of a later observer from an earlier callback, synchronous late registration inside a callback, and cancellation of an admitted later observer while the first callback is blocked on another thread. Cancellation in these dispatch controls did not suppress the later callback. See [dispatch evidence](../../../research/evidence/canvas-runtime-dispatch-2026-11-02/README.md). Callback admission, cancellation return and callback completion are distinct observations. Owned probe FD cleanup does not establish transport/render-resource cleanup.
