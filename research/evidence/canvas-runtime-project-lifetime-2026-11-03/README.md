# Owned project close/reopen and native weak liveness

Static discovery remains paused. One completed actual Xcode run exercises the previously untested owned-project close/reopen route, using the existing native weak collector. It is scoped native runtime evidence, not simulated replay, destructor verification or working WASM functionality.

The collector pins PID 45749's executable and PreviewsScenes SHA, verifies loaded framework UUID `afaf513ac1153755840e1d82b40e7d93` and Swift runtime UUID `7669d858d33236c79c6c4564ffbea8d2`, holds the controller lock, runs three owned ABI/FD controls and attaches existing probes. It finishes in 30.50 seconds of a 240-second budget. No helper dylib is loaded into Xcode; no protection, signing or process changes.

## Actual sequence and results

1. The owned PreviewLab.swift window starts with pin.fill. Native Pin Preview actions toggle to pin (observed) and back. Main-queue snapshots load guarded receiver token 1.
2. Native File > Close Project succeeds. The next accessibility read reports no accessible Xcode window. This is an AX observation, not a CG-window inventory or a destruction witness. The subsequent weak load of token 1 remains positive; no tracked destructor entry/return occurs.
3. Native File > Open… presents the remembered owned fixture directory, its PreviewLab.xcodeproj row and enabled Open button. Pressing Open reopens the owned PreviewLab.swift window. Snapshot now loads tokens 1 and 2. Token 2 is newly observed, not a proven new allocation or project/window owner.
4. Collection ends after **24 matched native pinning setter entry/return intervals**. Two probe weak slots are destroyed on main, hooks unloaded and Frida detached. The Xcode process remains alive.
5. Reopened Canvas is paused. After collection, one native Refresh Canvas press is acknowledged. Immediate observation has no declaration headers; a later bounded read shows pin.fill and the three original headers: Primary layers, Text and interaction, Layout edit. This proves the selected UI controls reappear. It does **not** prove pixel rendering, successful new build, private refresh callback ordering, provider completion or resource settlement. The visible Build Succeeded label predates this experiment and is not counted as a new build result.

The source and project hashes independently match their original bytes. Controller is available. Original window ID is not preserved across Close Project; owned source/project UI and selected pin/header state are restored instead. No user edits are discarded, and no user Xcode/simulator process is terminated.

## Evidence boundaries

| Existing recovered interface | Evidence exercised here |
| --- | --- |
| EditorScene pinningState.didSet, image offset 0x58e98 | Actual guarded native receiver observations and matched entry/return intervals; not complete setter-output parity |
| EditorScene deinitializing entry 0x5dcf8 | Existing static/interface qualification; zero tracked native entries or returns in this run |
| EditorScene deallocating entry 0x5e078 | Existing static/interface qualification; zero tracked native entries or returns in this run |
| Existing Swift runtime weak operations | Actual main-queue weak loads and probe-slot cleanup; temporary acquired strong references released on main |
| Canvas refresh after reopening | Native UI action and header-state observation only, after instrumentation detached; no private callback coverage |

The old receiver remains weak-loadable at sampled instants after project close and after reopen. Exact generic/project/window owner binding, who retains it and uninstrumented release timing remain unknown. Weak loads temporarily retain the receiver and can perturb timing. No leak, target destruction, observer cancellation during project close, renderer/transport/provider/global resource release, or fully working preview execution is established. Destroying our weak slot is only probe cleanup.

`events.jsonl` is the original address-free native stream; `ui.json` retains ordered selected owned controls/action acknowledgements. Full AX menus/sidebar/source stay local with input hash in provenance.json. Legacy snapshot label new-tab means before-project-close in this run; no new tab was created. Label restored means after reopen, before the post-collector UI refresh. The last snapshot is recorded in events.jsonl; its command output was not appended to the raw UI protocol. Initial raw-file serialization failed with a Python non-UTF-8 SyntaxError after collection, then the structured file patch preserved the in-memory protocol; no native result was changed. The earlier preparation-only run from the window checkpoint remains incomplete and is not retroactively upgraded.

## Reproduction

Start the existing `tools/re/native-canvas-runtime-weak-api/session.py` with the exact current Xcode PID, qualified owned helper/control paths, fresh output directory, and no file-cycle flag. Its ready marker, executable/image guard, exclusive controller lock and native-main acknowledgement are required. Use `tools/re/native-canvas-window-runtime/poll.py OUTPUT LABEL` to request the five existing labels in order, mapping new-tab to before-project-close and restored to after-reopen. Perform native accessibility actions only on the guarded owned fixture. On any save/discard modal, cancel rather than discard changes. Check the remembered Open dialog's owned directory/project before pressing Open; do not repeat the earlier unobserved keyboard route. Restore the owned project and UI, touch OUTPUT/stop and independently verify hashes/target/lock. Abort dependent actions on a failed guard or deadline.

Read retained evidence without executing Xcode:

```
python3 tools/re/native-canvas-project-runtime/verify.py research/evidence/canvas-runtime-project-lifetime-2026-11-03
python3 tools/re/native-canvas-project-runtime/check_reader.py
```

Eight synthetic corruptions reject. These are reader checks, not additional native tests. No original Rust/WASM code changes or full behavioral acceptance. Native complete areas remain 0/9; tracked issues 1/26 (3.8%). Next work should qualify exact ownership or instrument an existing refresh route during a guarded UI refresh, rather than repeat unchanged positive weak samples and infer destruction.
