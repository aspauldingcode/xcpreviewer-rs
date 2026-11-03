# Native Canvas window close and sampled EditorScene lifetime

Static discovery remains paused. This experiment uses actual Xcode accessibility actions and the existing guarded Swift-runtime weak observer. It is not simulated replay, a working WASM feature or complete destruction/resource acceptance.

## Observed run B

Xcode PID 45749, executable `/Applications/Xcode.app/Contents/MacOS/Xcode`, loaded PreviewsScenes UUID `afaf513ac1153755840e1d82b40e7d93`, Swift runtime UUID `7669d858d33236c79c6c4564ffbea8d2`. The existing collector checks the shipped framework SHA before attachment, holds the exclusive controller lock, bounds its lifetime to 240 seconds, and runs three owned ABI/FD controls first. No helper dylib is loaded into Xcode. Sources copied here are original instrumentation, not Apple implementation dumps.

Native AXPress toggles the owned fixture's Pin Preview glyph from pin.fill to pin and back. File > New > Window adds exactly one owned PreviewLab window; the original remains. The close button is selected from the added window's observed frame. Native inventory polling witnesses that window disappearing before the after-close weak snapshot. The final snapshot follows another 3.163 seconds later. The original window and pin.fill state remain.

The native pinning didSet probe records **43 matched entry/return intervals** and two guarded EditorScene-family receiver tokens. Baseline/unpinned weak snapshots load token 1; new-window, post-disappearance and final snapshots load both tokens. Temporary strong references from these main-queue weak loads are released on main. No tracked deinitializing/deallocating entry or return occurs. Final cleanup destroys two probe weak slots, unloads hooks and detaches. Source/project hashes independently match their original values; Xcode remains alive and the controller lock is available.

This establishes positive liveness **at the sampled load instants** after the added window disappears. It does not establish allocation counts, exact receiver-to-window/project ownership, a leak, uninstrumented release timing, or target destruction. A weak load temporarily retains its object and may perturb timing. Weak-slot destruction is probe cleanup, not EditorScene destruction or renderer/provider/transport settlement. The recovered destructor functions retain static/interface evidence only in this experiment because they were not exercised.

## Failures and incomplete controls

Run A performed the window actions, but its final requested snapshot followed the collector deadline; reading missing restored.json raised FileNotFoundError. Its immediate inventory still showed closing animation. It has no settled final liveness result and is not counted as a second passing lifecycle run. The collector itself cleaned up normally. A subsequent project-close preparation collector expired during coordinator delay, with no lifecycle action, snapshot or observed weak slot. **Project close/reopen destruction was not tested.** An Open-panel preparation merely reopened the already-owned fixture. A dispatched Go to Folder key chord was acknowledged but produced no observed dialog; keyboard delivery is unqualified and was not retried.

The initial synthetic close-original mutation accidentally targeted an index already occupied by the original window, so it changed no identity and was accepted. The mutation now replaces both created-window IDs with the original ID; eight actual corruptions reject. This is a reader-control correction, not a native failure or eight additional native controls.

## Reproduction

Use `tools/re/native-canvas-runtime-weak-api/build.py` for owned helper controls as documented by that tool. Run its `session.py` with the exact current Xcode PID and qualified helper/control paths, a fresh local output directory and **without --file-cycle**. Wait for ready; the collector owns the lock and enforces image/executable guards and bounded cleanup. Use native accessibility to verify only the owned PreviewLab fixture is current, remember original window ID/pin state, and perform the steps above. Request each of baseline, unpinned, new-tab, after-close, restored using:

```
python3 tools/re/native-canvas-window-runtime/poll.py OUTPUT_DIRECTORY LABEL
```

This waits for the collector's native-main acknowledgement, rejects ended sessions and duplicate labels, and fails after six seconds. Wait for added-window disappearance before after-close; wait at least three seconds before restored. Stop by touching OUTPUT_DIRECTORY/stop. Never close an unqualified/user window or discard edits. If a guard fails, preserve the failure and restore only owned UI state. The UI sequence requires an operator/approved native UI controller; there is no autonomous UI driver added by this change.

Recheck the published observation (no fresh native execution):

```
python3 tools/re/native-canvas-window-runtime/verify.py research/evidence/canvas-runtime-window-lifetime-2026-11-03
python3 tools/re/native-canvas-window-runtime/check_reader.py
```

`events.jsonl` is the original address-free native event stream. `ui.json` preserves ordered selected owned controls/action acknowledgements and inventory. Full AX menus/source trees stay local; their input hash is in provenance.json. Incomplete native streams and their limitations remain separately recorded. No rendered SwiftUI output, file/build refresh result, cross-platform runtime, or new full-contract acceptance follows. Native accepted areas remain 0/9; tracked issues 1/26 (3.8%).
