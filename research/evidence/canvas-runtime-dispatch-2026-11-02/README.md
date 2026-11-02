# Native observer dispatch mutation and cancellation controls

Static expansion remains paused. Two fresh owned-process runs each passed all **eleven normal shipped PreviewsFoundationHost controls**, including three new deterministic dispatch cases. This is actual native component execution through the existing qualified ARM64 adapters, not a simulated observer model, static replay or native Canvas UI session.

| New native control | Exercised result |
| --- | --- |
| Earlier observer cancels later observer's token inside its callback | Cancel returned; later observer still ran once after the first callback's cancel section |
| Earlier observer registers another observer inside its callback | Newly registered observer ran synchronously before add returned, returned no token, and preceded the remaining original observer |
| First observer blocked on worker; main thread cancels later observer before its callback | Cancel returned while later context/owned FD remained alive/open; after unblocking first observer, later callback still ran on worker |

The third case directly distinguishes cancellation return from suppression of a callback that had not yet started. It does not imply cancellation can never prevent callback delivery: the existing pre-invalidation cancellation control still suppresses it. The nested registration order in both runs was A → nested late observer → B; no general scheduling/fairness claim follows.

## Callback lifetimes and release evidence

Each Probe owns a `/dev/null` sentinel FD. Swift weak references and fcntl EBADF checks supplement explicit deinit/close logs. All new normal controls checked weak references cleared and owned descriptors closed after native invalidate returned. The recorded traces additionally show deinit/close before that return. Nested late observer cleanup occurred after its add returned and before the enclosing callback continued to the next original observer. In the cross-thread case, the later context remained alive/open after cancel returned while the first observer was still blocked, then callback and cleanup occurred before invalidation completed.

Exact relative destruction order of the original A/B contexts is not imposed as a contract. It differs across controls; assertions require actual cleanup and the observed boundary, not an invented universal array-destruction order. Native storage admission/fulfilled-state interpretation comes from the already recovered invalidation transfer source; the tests directly establish callback/cancel/add/return order and owned-context outcomes.

## Reproduction and identity

Run `python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-fresh` from repository root. Output must be new. The runner copies original source/adapters, strips DYLD overrides for children, pins the on-disk PreviewsFoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d` and asserts loaded path/UUID `6b75229bde5d3d3794bc75af4f4704c6` and known metadata/symbol offsets. Native sessions hold the exclusive controller lock. Compiler subprocesses have 30-second bounds; each owned native process has an eight-second bound with owned process-group cleanup. No user Xcode process is attached, invoked, terminated or modified by these component tests.

initial/ and reproduced/ retain exact executed source/adapters, execution verifiers, compiler/case receipts and stdout/stderr. Binaries, object files, module caches and Apple code dumps are excluded. The final root verify.py strengthens new-case deinit-before-invalidate-return assertions against those same executed traces; exact originally executed verifiers and their hashes remain under each run/receipt. Canonical native source matches the executed source. No new functions or static research areas were recovered.

Both full captures pass final assertions. Six semantic altered-trace controls reject: suppress admitted callback, defer nested callback until after the enclosing add section, close FD before delivery, move callback before cancel returns, claim incomplete cleanup, and move destruction after invalidate return. Sequence numbers/timestamps are normalized in these **synthetic trace mutations** so behavior assertions, not accidental numbering errors, reject them. They are not extra native executions.

## Scope and failures

No native case failed, timed out or crashed in these two normal runs. The previously observed destructor-reentry recursive-lock termination remains separate historical negative evidence; it was not rerun here. The prior eight cases passed regression checks, including 100 concurrent rounds per run. Those 200 sampled rounds are not general race-freedom proof. Existing [in-flight/concurrency evidence](../canvas-runtime-concurrency-2026-11-02/README.md) and [initial runtime failures](../canvas-runtime-validation-2026-11-02/README.md) remain independently scoped.

Owned FD/context cleanup does not establish final Mach/XPC/IOSurface/render-resource release or every native closure lifetime. No Canvas UI, native build/file refresh, private Preview.update, SwiftUI state continuity, rendered completion or cross-platform WASM behavior was exercised by this package. The native-window limitation was not retried. No Rust product changes or Rust tests occurred. Full native area acceptance remains 0/9; tracked delivery remains 1/26 (3.8%).
