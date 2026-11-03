# Failed native counter-interaction qualification and target crash

Static expansion remains paused. The intended experiment was to select the owned Text and interaction preview, exercise its Increment button, then measure state continuity through updates. **That experiment did not run.** No counter value, counter callback, interactive state transition or state preservation is verified.

## What actually happened

The initial native AX read qualifies Xcode PID 45749 and the owned PreviewLab.swift window. Original screenshots show the selected Primary layers preview, not the counter preview. The Text and interaction tab appears as AXStaticText. Its advertised CLICK operation is not an AXPress: the attempted semantic click fails with `offers no AXPress; it has []`. A second owned-window screenshot still shows Primary layers. This is an input-interface failure, not a SwiftUI button failure.

The agent then incorrectly used the **marker-based** `visual_click` operation with requested coordinates (1116,136) taken from the tab's observed AX frame. The operation instead reports a marker at (47,14) and actual click (95,58). That point lies inside the recorded Xcode Full screen control frame [87,51,16,16], outside the intended tab. Supplied x/y did not constrain this marker operation. The response says HID/real pointer and changes the reported frontmost PID. This fallback was a mistake; it is not qualified tab selection or preview input delivery. **Do not use visual_click as a coordinate fallback. Do not retry this window-control click.**

Subsequent old-target AX requests have no accessible window; capture has no on-screen Xcode window. A bounded native activation reports success but no AX restoration. File > Open recovery fails with no menu bar exposed. One Ctrl-Cmd-F recovery key receipt reports CGEvent→pid success, but the following AX read still fails. The key receipt exposes a different frontmost PID, not its resolved target PID. Target continuity was not requalified before this key attempt; its delivery and effect are unverified. No further pointer/keyboard actions are taken after discovering the target change. A later public LaunchServices project-open request is separately guarded to the new PID and exact owned project, as described below.

## Confirmed process failure and new identity

Independent process qualification later finds PID 45749 absent and a new Xcode main process, PID **64394**. A local diagnostic report confirms the old PID crashed with EXC_BAD_ACCESS/SIGSEGV, termination signal 11. Selected faulting-frame symbols include event/control mouse tracking and `_NSThemeZoomWidgetCell` tracking. The reported bad click lies in the window Full screen control area; the crash is temporally associated with this input attempt. A causal mechanism is **not** established. The same old process had been instrumented in previous checkpoints, although no Frida hooks were attached by this experiment. The role of prior instrumentation, window-mode changes and other concurrent factors is unknown. No crash reproduction was attempted, and no termination/kill command was issued.

A later native inventory is inconsistent: app lookup still reports Xcode PID 45749 while its window inventory shows PID 64394 with **Welcome to Xcode**. Bundle-targeted AX lookup continues to fail. This is a concrete tool/target identity mismatch; it does not establish that the new process has no window or that the session is locked. Public session metadata again has an absent screen-lock field, which proves no lock state. Native activation was requested during recovery, but the exact relaunch mechanism was not independently observed. At this stage, original owned project/window restoration was not verified. Subsequently, a public `/usr/bin/open -a /Applications/Xcode.app` request for the exact owned PreviewLab project returned zero under a fresh controller lease after requalifying PID 64394. The first native inventory shows an initializing blank window; the settled native window inventory then shows only PreviewLab — PreviewLab.swift in PID 64394, frame [23,33,1401,902], matching the original window geometry. This verifies owned project/window-title restoration, not exact Canvas/pin/counter state. App lookup still reports the stale old PID; no further target UI testing is attempted.

The initial postflight packaging guard assumed the old PID would exist and failed on ps status 1; the first artifact reader then failed because postflight.json was missing. The corrected receipt explicitly retains old-target absence/new identity instead of claiming the target alive.

## Preserved work and evidence levels

Source and project SHA-256 still match their original bytes. This experiment made no source/project edits and injected no instrumentation. The exclusive controller leases ended and independent lock acquisition succeeds. No user edits were discarded, no signing/protection/permission change was made, and no Xcode/simulator process termination was requested. These data-integrity checks do not claim exact Canvas/window-mode/state restoration. The later owned window-title/geometry observation is separate from those checks.

- Static reconstruction: no new function recovery.
- Simulated replay: none accepted as native. Four synthetic corruptions only test this failure-record reader.
- Native observation: original owned-window screenshots and AX/action receipts, actual target-identity checks and sanitized crash-report metadata.
- Verified runtime functionality: no new counter interaction, state continuity, destruction/resource cleanup or WASM feature. A crash is a failure, not lifecycle acceptance.

Full native areas remain 0/9; tracked issues 1/26 (3.8%). This checkpoint supersedes the earlier assumption that the old native target/window remains available. Keep all earlier positive observations scoped to their captured PID/version/time. Do not attach to a guessed PID or act through the stale bundle lookup. UI work needs current explicit target qualification and a safe input route. Meanwhile existing owned-process controls and portable validation remain permitted; broad static expansion stays paused.

## Artifacts and checks

`before.jpg` and `after-tab-failure.jpg` show only the owned fixture's Xcode window. observations.json retains selected controls/action receipts; it omits full AX menus/source trees and unrelated process inventories. crash-summary.json publishes only selected metadata/symbols and the hash/location of the local raw report, with no raw addresses/full private dump. new-target.json preserves only the earlier Xcode app/window identity discrepancy. launchservices-recovery.json preserves the later guarded request and owned window-title/geometry restoration, with Canvas state explicitly unknown. The raw native report stays local.

These commands validate the retained failure record; they do not reproduce native input or the crash:

```
python3 research/evidence/canvas-runtime-interaction-qualification-2026-11-03/verify.py research/evidence/canvas-runtime-interaction-qualification-2026-11-03
python3 research/evidence/canvas-runtime-interaction-qualification-2026-11-03/check_reader.py
```

There is intentionally no automatic reproduction driver for the mistaken marker click. Future experiments must treat tool acknowledgement separately from intended target delivery, requalify process identity after unexpected focus/window changes, and stop dependent UI actions on mismatch.
