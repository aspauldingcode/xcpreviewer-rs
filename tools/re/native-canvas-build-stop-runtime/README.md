# Native build-stop loaded-false preference control

This observational macOS/arm64 test runs the existing real success → intentional source-error failure → exact-restoration recovery build sequence. It observes the loaded auto-resume Bool and build-success payload at the recovered native AND instruction, then the following return path. It does not change preferences, invoke private handlers directly or force a branch.

Use the prerequisites and explicit owned fixture selection from the [build listener controls](../native-canvas-build-runtime/README.md). Run from repository root with the owned project active in Xcode:

```sh
python3 tools/re/native-canvas-build-stop-runtime/run.py \
  --output /private/tmp/canvas-stop-gates-fresh \
  --pid XCODE_PID \
  --workspace /absolute/repo/research/build/preview-workspaces/FIXTURE/PreviewLab.xcodeproj \
  --source /absolute/repo/research/build/preview-workspaces/FIXTURE/Sources/PreviewLab/PreviewLab.swift
python3 tools/re/native-canvas-build-stop-runtime/verify.py /private/tmp/canvas-stop-gates-fresh
```

Output must be new; the primary source must match the known digest. Exclusive controller lock, loaded/on-disk image checks, exact active-workspace guard, bounded Frida stages and 25-second AppleScript build bounds apply. Source replacement/restoration checks concurrent edits; unexpected edits are preserved. Xcode is not terminated. A pending build is not killed. On interruption outside finally cleanup, compare the retained source backup and current bytes before restoring anything.

The register observation at 0x2496dc is qualified by existing source anchors: 0x2496d8 loads the generic Bool output into w8; 0x2496dc ANDs it with w27's event payload. The agent reads x8/x27 low bits before that instruction. It also records existing scene/state gates and coalescer/scene entries when traversed. Return-path attribution uses enclosing handler IDs, since the target at 0x24a088 is shared with other routes. A single preference-input probe avoids the unresolved adjacent-probe reporting limitation retained in the evidence.

The verifier intentionally qualifies the observed **loaded-false** environment. A future true value is a different test outcome and must not be silently accepted as false. This does not establish a persisted key, factory default, UI preference setting, true-preference branch, scene/state gates, automatic resume or rendered completion. See [executed traces and incomplete capture](../../../research/evidence/canvas-runtime-build-stop-gates-2026-11-02/README.md).
