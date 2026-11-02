# Native observer runtime tests

Execute shipped PreviewsFoundationHost, not a model. See [runtime evidence](../../../research/evidence/canvas-runtime-validation-2026-11-02/README.md) for scope and failures.

Run from repository root: `python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-fresh`

Add `--include-negative-control` to intentionally exercise destructor reentry termination in an owned child. Output must be a new directory. No user Xcode process is injected or terminated by these component tests.

The default suite now includes eight normal controls: in-flight cancellation and 100 four-operation concurrent rounds supplement the original six. See [concurrency traces](../../../research/evidence/canvas-runtime-concurrency-2026-11-02/README.md). Cancel returning does not imply that an already active callback has finished.
