# Real Preview.update execution and Canvas color update

Static expansion remains paused. The old user Xcode PID 5841 was no longer running. A bounded exclusive-controller session opened the owned PreviewLab fixture in the background with `open -g`; new PID 45749 had an accessible window. No existing Xcode process was terminated or replaced. The native Refresh Canvas button was pressed through AXPress, with `took_focus=false` and unchanged foreground PID. This recovered a useful native route after the earlier no-window limitation.

## Actually exercised behavior

Selected Primary layers initially rendered a purple body. A real external edit changed only its blue source constant from 1 to 0. During that edit's attached capture, pinned PreviewsScenes `Preview.update(withItem:)` at 0x3f694 entered/returned **18 times**, and the selected PreviewsUI assignment helper at 0x19dd4 entered/returned **18 times**, with nested balanced calls on one observed thread. Helper caller offset was 0x3f978, matching the previously recovered instance-assignment path. These counts are observations, not a one-call-per-edit/preview contract. Arguments/item identities were not decoded and no object lifetime is inferred from value storage.

The actual selected native preview changed visibly from purple to brown. Exact source bytes were restored; after detachment, native output returned to the prior purple body. A second cycle in the **same previously attached process, with no active hooks**, repeated the same color change and restoration. It is not a pristine never-instrumented control or general observer-transparency proof.

This combines native method execution evidence with a native UI source-to-render control. It is not simulated replay, portable renderer output or a successful build being treated as rendering proof. Only this selected live preview-content path is qualified; missing canvas, registry, non-preview and unexpected-case guards, item-setter internals, notifications, session continuity and resource settlement remain open.

## Screenshots and assertions

Unmodified native window JPEGs are included; the screenshot tool reported window ID 13118, scale 1.401 and 1000×644 output. The selected preview body ROI (790,340)-(816,354) was chosen by visual inspection, excluding editor text and title chrome. Baseline mean RGB was approximately [122.95,80.04,126.00]; changed mean [122.17,80.90,18.95]. Both changed captures have identical decoded ROI bytes; attached-restored and repeat-restored ROI bytes match baseline. This is a lossy screenshot-region comparison and visible color-change assertion, **not exact native render-buffer/pixel parity or color-management qualification**.

The repeat's early-after-edit screenshot still showed old purple output; the later changed screenshot showed brown. No exact refresh latency, debounce boundary or stale-state enum is inferred. The selected scene has no interaction-state test; SwiftUI counter/focus/state preservation remains unverified.

verify.py checks pinned loaded UUIDs in the hook receipt, actual source-edit hash, balanced/nested method entry-return events and caller, source restoration, no-active-hook session metadata, screenshot geometry and ROI change/restoration. Five synthetic artifact mutations reject: wrong caller, missing return, unchanged output, unrestored output and false source restoration. Those checks do not rerun native Xcode. Exact executed helpers, agent, UI tool receipts, launch/controller records and JSONL traces are preserved. Native scripts and function pins derive from [existing Preview.update source evidence](../canvas-preview-update-2026-11-02/README.md); no new functions were discovered.

## Preserved limits and failures

The initial startup/refresh capture recorded no selected method calls and is not used as Preview.update qualification; the later real edit capture supplies that evidence. AXPress on the Layout edit static text failed because it offered no AXPress action. No blind click or repeated unsupported press followed; the control stayed on the visually verified Primary layers preview. Its failed UI receipt is retained. No native app crash occurred.

Compiler/cache/JIT artifacts, Apple binaries and raw private dumps are not published. Screenshots show only the owned project/window. Source restored SHA-256 is `128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef`. Final independent check found controller available and Xcode 45749 still alive; it is left running. Source mutation/attached and repeat sessions held the controller lock with 120-second deadlines and conditional restoration. Frida operations were bounded. No system protection, signing, purchase or user Xcode/simulator termination occurred.

Reproduce through tools/re/native-canvas-preview-runtime/session.py with the documented operator UI/screenshot steps. Current bounded function coverage is indexed separately in research/loop/canvas-runtime-function-coverage.json; untraced functions remain static. No Rust product changes or Rust tests. Full native areas remain 0/9; tracked delivery 1/26 (3.8%).
