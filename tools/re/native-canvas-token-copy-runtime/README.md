# Native cancellation-token value-copy controls

Run only on the qualified macOS/arm64 installed Xcode profile:

```
python3 tools/re/native-canvas-token-copy-runtime/run.py --output /private/tmp/NEW-OUTPUT
python3 tools/re/native-canvas-token-copy-runtime/verify.py /private/tmp/NEW-OUTPUT
```

Output must not exist. The runner copies original instrumentation, compiles owned Swift/assembly/C sources, executes an owned 24-byte value-copy ABI control first, then five native token-copy modes. ABI failure stops subsequent cases. Each native child holds the controller lock, pins the shipped framework SHA/loaded UUID/symbol interfaces and has an eight-second deadline. Only owned compiler/test child groups may be terminated by their deadline; no user Xcode/simulator process is accessed. No private Apple binaries or compiler cache belong in publication.

The new interface is runtime metadata table slot +16, qualified through an owned three-reference value and then exercised on the existing 24-byte cancellation-token type. No new native function body is recovered. Native copy resolves to the pinned image offset 0x12a0ec; the reader checks that observation. The callback for copy-inflight compares raw context identity and records strings/semaphores without constructing a strong Probe local.

Modes: copy-invalidate, copy-cancel, copy-drop-both, copy-owner-loss and copy-inflight. They distinguish token destruction from cancellation, cancellation through either value from duplicate registration, owner loss from token retention, and blocked callback lifetime from token storage lifetime. Probe weak references, actual descriptor close/EBADF checks, callback count/order and owning thread are measured. They do not measure native reference counts or renderer/provider/global resources.

The original compile diagnostics retain WeakMutability and a legacy global-function Sendable warning in default Swift compatibility mode. This harness does not claim Swift 6 strict-concurrency acceptance. Native assertions and semantic evidence readers must pass; successful compilation alone is insufficient.

Retained qualified B/C runs and preliminary A's callback-local-retention confound are documented in research/evidence/canvas-runtime-token-copy-2026-11-03. No user application UI, stale bundle lookup, raw private dump, signing/protection change or static expansion is required by this route.
