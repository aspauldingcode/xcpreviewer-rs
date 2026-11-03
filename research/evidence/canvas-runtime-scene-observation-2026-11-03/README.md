# Weak-helper boundary and actual EditorScene class observations

Static expansion remains paused. This experiment attempted a real class-lifetime measurement rather than using value-witness counts as object-death evidence. Minimum interface qualification identified the already-known EditorScene class and exact pinning observer, removed-file update and class destructor symbols. No new bodies were decompiled or recovered. The target remained Xcode PID 45749 with pinned PreviewsScenes image/UUID.

## What actually works

An original Swift weak-box helper and C caller passed three standalone controls: weak target clears and owned FD closes after release; an extra strong reference keeps target/FD alive until final release; disposing the weak box while target lives does not close the target's FD. Runtime object_getClassName recognizes the owned pure Swift fixture. The reproducible build.py ran these controls under the exclusive controller lock; each native capture also ran them under that lock. This is working **owned fixture** weak/FD behavior, not Xcode EditorScene lifetime verification. Only original source, logs and hashes are published; compiled binaries remain local.

Two permitted file-only native captures added/restored an original declaration in the owned source. They recorded **20 and 22 complete pinningState.didSet intervals**, all on the observed main thread, with a runtime class-name guard matching the EditorScene family. Each capture first observed one address-correlated receiver token. The guard is a family predicate at a known instance-method entry; exact generic type and per-instance project/document binding are unqualified. The earlier Preview.update value receiver was not treated as a heap class object.

No selected deinitializing, deallocating or removed-file method entries were observed. The source-only changes did not close a window/document, and UI closure controls were not executed. This does not demonstrate retention, a leak, object survival after a snapshot, or absence of unobserved release paths. Snapshots read the agent's event ledger; they are not native weak loads. Address reuse without an observed destructor could merge observations, so tokens are not permanent object identity. The native class weak/reference-lifetime and resource-release contracts remain unverified.

## What fails or could not run

Xcode rejected Module.load of the owned helper: mapping process and non-platform file have different Team IDs. That attempt was stopped; no protection was changed and no Apple app was re-signed. Its exact agent, error receipt and source are retained in load-blocked. The original helper logged failure but returned zero; this is preserved, not accepted as a passing test. Current helper failures return nonzero; an actual wrong-target guard control exited one before Xcode attachment. The unchanged load rejection was not retried.

CUA then reported the Mac locked on the owned-window state request. No pin, new-window or close-window action was executed, and no unlock bypass was attempted. The observational session without a source edit therefore supplies no class-lifetime control. Work switched to explicitly authorized owned file changes with native observation; there is no new native rendered-UI claim. The screen lock still blocks the unexercised GUI lifetime route, but repository/CLI source tests can continue.

An initial unawaited launcher produced no receipt and is excluded. A direct awaited launch supplied the recorded helper-load failure. The capability flag weak_reference_access_available=false describes the implemented observer route; it is not a claim that every existing runtime weak API is unavailable. No alternate native weak API route was qualified here.

## Evidence and cleanup

Native captures hold the exclusive controller lock and pin executable, framework hash/UUID and exact source bytes. Compiler/native/ack waits are bounded. The class-name API was qualified on the owned Swift fixture before use at the known class receiver; exact symbol boundaries were checked with nm. Owned emitted IR provides a Swift-self ABI reference for fixture destructors, not evidence that the target destructors ran.

The two completed captures restored source SHA-256 128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef, detached listeners, created zero native weak boxes and performed no helper load. Script/session cleanup completed, controller was independently available and Xcode remained alive. Detach receipts are not a general in-flight callback-drain guarantee. Framework caches/UI state are not claimed to be restored bit-for-bit. Raw native object addresses, Apple binaries, private dumps and disassembly are not published.

verify.py checks real fixture assertions, loader rejection, unexercised UI state, nonzero wrong-target guard, paired native method records, class predicates, snapshot limits/scopes and source restoration. Eight synthetic artifact mutations reject; they do not rerun native code. Fifteen native observer-suite controls remain separate prior evidence. No Rust product changes/tests or accepted areas. Full native areas remain 0/9; tracked delivery remains 1/26 (3.8%).
