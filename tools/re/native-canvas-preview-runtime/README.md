# Native Preview.update and rendered color control

Requires the pinned running Xcode profile, owned PreviewLab fixture active, live Canvas selected on **Primary layers**, and visually confirmed baseline purple output. This is an operator-coordinated native UI control. Do not launch/replace an unknown existing user workspace. Record the exact target PID/window and current screenshot geometry first.

```sh
python3 tools/re/native-canvas-preview-runtime/session.py \
  --output /private/tmp/canvas-preview-fresh --pid XCODE_PID \
  --source /absolute/repo/research/build/preview-workspaces/FIXTURE/Sources/PreviewLab/PreviewLab.swift
```

Wait for `ready` in the new output directory. Record baseline using the native computer-use screenshot tool; touch `edit`, wait for `edited`, and observe until the actual preview changes. Record another screenshot. Touch `restore`, wait for `restored`, and observe the original output return before touching `stop`. The session has a 120-second deadline and conditionally restores exact original source in finally cleanup. Unexpected concurrent edits are preserved, not overwritten. The exclusive controller lock spans attachment, source mutation, UI observation interval and cleanup. Source/workspace identity, on-disk image hashes, loaded UUIDs for attached sessions and exact process path are guarded. Frida operations have independent bounds. Never terminate Xcode as cleanup.

Repeat with `--no-hooks` to measure output with no active probes. A previously attached process is not a pristine never-instrumented process; record that distinction. Screenshot selection remains an operator step because an early screenshot can still show the old output while refresh is pending. Keep unmodified screenshot files and tool receipts. For the published geometry, an inspected body-only ROI was (790,340)-(816,354) in 1000×644 JPEG captures. Reinspect geometry before reusing that ROI; this is not a universal coordinate.

The attached agent observes the already recovered PreviewsScenes Preview.update entry/return and the selected PreviewsUI value-assignment helper called from offset 0x3f978. It does not decode item payloads, identify class objects from value-storage addresses or prove lifetime/state continuity. See [traces, native screenshots, failed AX action and scoped coverage](../../../research/evidence/canvas-runtime-preview-update-2026-11-02/README.md).
