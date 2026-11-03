# Native EditorScene weak loads through the existing runtime

Static discovery remains paused. This experiment converts the previous address-only receiver ledger into actual Swift weak storage using already-loaded runtime exports. It does not load a helper image into Xcode, change protections, re-sign Apple software, or retry the previously rejected loader. The owned dylib runs only in a separate owned C control process. This is a different permitted observation route; the prior Team-ID failure remains recorded.

## Native execution actually exercised

The direct C controls resolve swift_unknownObjectWeakInit, WeakLoadStrong, WeakDestroy and unknownObjectRelease from libswiftCore. All three owned controls pass: final release clears weak storage and closes the owned FD; an additional strong reference postpones that outcome; destroying the weak slot while the target is alive leaves the FD open until target release. The control verifies an eight-byte slot and the main-queue export address. A fresh source build reproduces these three passes. Existing original Swift fixture compilation supplies the representation; no Apple object is fabricated.

Two serial captures in Xcode PID 45749 each perform an actual owned source declaration addition and exact restoration. Both record **25 paired pinningState.didSet intervals** and one EditorScene-family receiver. At that known receiver entry, the class/main-thread guard passes and actual weak storage is initialized. File-added and file-restored main-queue snapshots each successfully load a strong reference through that weak storage, then release the obtained strong reference. Each capture destroys one probe weak slot on the main queue. The runtime UUID is 7669d858d33236c79c6c4564ffbea8d2; PreviewsScenes UUID is afaf513ac1153755840e1d82b40e7d93. Executable/framework identities and source SHA are guarded before target mutation.

These are **positive weak loads at sampled instants**, not permanent address identities or a claim that the object survives after release of the temporary strong reference. The probe itself can perturb release timing. No strong reference is intentionally held across samples. Destruction of the probe's weak slot is not destruction of EditorScene. Exact generic/project binding remains unqualified.

## Failures, limits and unknowns

There is no selected native EditorScene deinitializing/deallocating entry in either run and no nil weak result. Consequently target destruction, weak zeroing after target release, reference-count balance of the whole target, and transport/render resource release remain **unverified**. No window/document-close or pin control was executed. The prior locked-Mac UI failure was not retried, and no new rendered output or interactive state continuity is claimed. Real file mutation exercises the native setter route only; it is not a build-notification test. Prior build/observer evidence remains separate.

Both normal captures finish without logged script/native error or timeout. An actual wrong-executable control exits one before attachment. The first run's original session has no explicit unload/detach success messages; it returns normally after those bounded calls. The second session adds explicit receipts and makes cleanup/unload errors fail the process. Both exact executed session sources are preserved. No generic callback-drain guarantee is inferred from detach.

Eight synthetic recorded-evidence faults reject (wrong runtime, unexpected helper load, non-main sample, failed class guard, nil sample, unmatched return, missing slot destruction, failed source restoration). These are reader tests, **not native failure injections**. No native nil/deinit positive control on EditorScene has been obtained.

## Evidence levels and postconditions

* Native runtime verification: owned three-mode ABI/FD controls and two real-file Xcode weak-load/setter captures, with original execution agents, structured logs and captured-order assertions.
* Static qualification: minimum existing symbol/receiver and owned compiler representation needed to run these controls. No broad new function recovery.
* Simulated replay: none used as native proof; synthetic faults only validate the artifact reader.
* Working functionality: original diagnostic harness on this pinned host. No standalone WASM feature or cross-platform SwiftUI parity acceptance follows.

Source restored to SHA 128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef, hooks/scripts detached, controller independently available, Xcode left alive. No binary, private native dump or raw receiver address is published. Event times are normalized to each capture's first receipt; the remaining event payloads are unchanged. Native rendering/resource acceptance remains 0/9; milestone counts and tracked delivery remain 1/26 (3.8%).
