# Native positive selection and scene-update method control

Two serial native runs converted the existing recovered late modified-file route into a positive runtime control. Each temporarily added an original Swift file and target-member reference to the owned PreviewLab project, without opening that file through the harness. The added enum's constant is not referenced by the preview. Each real build completed with `true, succeeded, true`: completed, successful, and build log contained RuntimeRefreshDependency.swift. This Boolean is a log marker, not proof that the constant was executed or rendered.

After build completion and a three-second wait, each run changed the constant from 1 to 2, then restored it to 1 in a separate phase. The actual native trace for **each of four file-change/restoration invocations** was:

1. Modified timestamp presence, time-check and late pass path.
2. Modified-file filter entry.
3. `isOpenAndThunkable` returned false.
4. `shouldUpdateModifiedFile` returned true.
5. Environment coalescer setNeedsUpdate entry.
6. WorkspaceScene.setNeedsUpdate entry and return.
7. Enclosing workspace-handler return.

This complements the separate [negative open/thunkable selection and early suppression controls](../canvas-runtime-file-timing-2026-11-02/README.md). The fixture and path differ intentionally: these runs use a second target member absent from the preview's referenced code. No forced Bool, synthetic notification, preference mutation or clock patch was used. A bounded two-second no-action baseline preceded fixture installation and had no modified-path probes.

## Native attribution

The source anchors are the existing [modified selection](../canvas-modified-files-2026-11-01/README.md), [thunkable refresh](../canvas-thunkable-refresh-2026-11-01/README.md) and [time gate](../canvas-build-time-gate-2026-11-01/README.md) evidence. Static expansion remains paused; no new functions were recovered.

The same full PreviewsXcode/PreviewsIDEAPI file hashes and loaded UUIDs are pinned by the driver/agent. Observations use previously recovered block/function offsets, the existing environment coalescer entry at 0x4f43c, and the existing exported WorkspaceScene.setNeedsUpdate method in loaded PreviewsScenes. No private method is directly invoked by the harness. The second run recorded direct callers: coalescer return address offset **0x249c84** and scene-update return address offset **0x24a2ec**, matching the earlier recovered calls at 0x249c80 and 0x24a2e8. Per-thread enclosing-handler identifiers bind predicate, coalescer and method observations to the same invocation. The earlier block probe at 0x24a264 was not traversed in these positive invocations; the resolved method-entry probe and recorded caller establish actual call execution independently of that block's entry.

`initial/` and `reproduced/` retain exact original executed agents/drivers, commands, messages and build receipts. `assertions.json` records both passing capture checks and nine rejected altered-trace controls: predicate, coalescer, scene call/return, caller, project restoration, dependency absence, phase and build-log marker. The altered traces are verifier checks, not extra native executions. `verify.py` is a recorded-assertion reader, not a native rerun. Reproduce using tools/re/native-canvas-passing-file-runtime.

## Cleanup and limits

An exclusive controller lock covered fixture creation, attachment, build, writes and teardown. Exact original primary source/project hashes were required before mutation. Concurrent-file guards protected project/file removal; both runs restored project bytes and removed only the created dependency file. Local backups remain in the run outputs. Frida stages and real AppleScript builds had deadlines. Both finally receipts report source/project restored, dependency absent and hooks detached without terminating Xcode. An independent cleanup check found Xcode PID 5841 still alive, controller lock available, original source SHA-256 `128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef`, project SHA-256 `1ee671965dcfb221233970e970130946a1971a0b0d30625601e93440a60bcf45`, and no created dependency file. No native crash or harness failure occurred in these runs.

These observations establish native positive selection and actual coalescer/scene-update method execution and return. They do not establish queue drain, accepted update payload/reason, asynchronous refresh completion, preview recomputation, changed rendering, persistent SwiftUI state, cancellation/resource settlement or arbitrary-target coverage. The new constant was deliberately unreferenced; no meaningful rendered delta was expected or checked. Notification payload/file URL arguments were not decoded; file-event attribution is the controlled one-file write and matching phase/handler route. No Foundation.Date values or exact two-second boundary were measured. Native hooks affect timing.

Native code executed on one owned macOS fixture/profile; standalone Linux/Windows/WASM SwiftUI remains open. Earlier observer lifetime/build-failure controls were not rerun. No Rust product changes or Rust tests. No Apple instructions, binaries or raw private dump is published. Full native area acceptance stays 0/9; tracked delivery stays 1/26 (3.8%).
