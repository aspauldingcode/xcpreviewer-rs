# Qualified native log(String) runtime controls

Run from the repository root (new output directory required):

```sh
python3 tools/re/native-canvas-log-runtime/run.py --query-log-store --output /private/tmp/canvas-log-fresh
```

This uses an existing field descriptor only to qualify the previously recovered log case's associated type `(message: Swift.String)`. The runtime resolves that type and checks its size. The input uses a real Swift short string, not zero-filled String storage. No broader static discovery occurs.

The runner builds the original owned-process adapter and executes fulfilled/unfulfilled controls without instrumentation, with a stdin gate but no attachment, and with observational Frida hooks. Compiler stages have 30-second deadlines, native controls eight seconds after release of the gate, and attachment/load stages their own cancellation bounds. All native sessions use the exclusive controller lock. Only owned children can be killed/reaped on deadlines; Xcode/simulators are never attached or terminated.

With `--query-log-store`, bounded read-only queries select exact owned PIDs and publish only matching owned diagnostic/compose-failure messages. The gate alone did not prevent readable native records. Frida entry-only and earlier entry/return logging probes both produced stored compose failures in the exercised setup, despite normal process return. Hook observations establish API invocation, not undistorted logging output. Backend delivery claims rely on readable **unattached** records. Receipt `os_log_persistence_verified` means immediate matching-PID record retrieval only; long-term durability is not tested.

This is one short-string fixture on a pinned native image, not general String ownership, assertion delivery, full Canvas/UI/resource parity or cross-platform WASM. See [evidence and observer-effect controls](../../../research/evidence/canvas-runtime-log-delivery-2026-11-02/README.md).
