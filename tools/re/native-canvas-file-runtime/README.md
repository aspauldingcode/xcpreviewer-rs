# Native file-event timing controls

Observational Frida instrumentation on macOS/arm64 exercises existing recovered Canvas code through actual disk writes. It runs one real build, appends a harmless comment shortly after the native build timestamp path executes, then writes a different comment after build completion plus three seconds. It restores the original source and observes the restoration event too. A two-second no-action baseline precedes the build.

Use the same pinned Xcode, owned active fixture, existing Python Frida bindings and explicit process selection as the [build controls](../native-canvas-build-runtime/README.md). Run from repository root:

```sh
python3 tools/re/native-canvas-file-runtime/run.py \
  --output /private/tmp/canvas-file-fresh \
  --pid XCODE_PID \
  --workspace /absolute/repo/research/build/preview-workspaces/FIXTURE/PreviewLab.xcodeproj \
  --source /absolute/repo/research/build/preview-workspaces/FIXTURE/Sources/PreviewLab/PreviewLab.swift
python3 tools/re/native-canvas-file-runtime/verify.py /private/tmp/canvas-file-fresh
```

Output must be new; fixture source must match the known original digest. The controller lock covers attachment, mutation, build and restoration. Each build checks Xcode's active project. Concurrent user edits prevent destructive restoration. Frida stages are bounded; the real AppleScript build has a 25-second process deadline. No Xcode termination occurs. If interrupted outside Python finally cleanup, inspect the retained source backup before restoring anything.

The agent adds observations at previously recovered native basic-block entries, grouped by enclosing workspace-handler invocation. It reads Bool returns from the existing membership/selection predicates. It does not inject synthetic workspace notifications, alter timestamps, force branch outcomes or change return values. Hooks alter execution overhead. The early write may arrive too late on a different machine; a failing early-path assertion is an observed control outcome, not permission to relabel a passed branch as suppressed.

The verifier requires actual recorded suppression before filtering for the early event, the time-pass/filter path for late and restoration events, balanced handler return, and exact restoration/detach receipts. When membership hooks are present, the recorded open/thunkable=true and should-update=false results are required. These are observations for this fixture, not expected results for arbitrary files. It does not claim exact two-second boundary measurement, a refresh timer, refreshed rendering, all-target parity or resource release.

See [executed evidence and limits](../../../research/evidence/canvas-runtime-file-timing-2026-11-02/README.md).
