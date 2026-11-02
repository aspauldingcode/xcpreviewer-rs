# Actual Xcode build listener runtime control

This macOS/arm64 test attaches observational Frida hooks to an explicitly selected running Xcode process. It runs three real builds in an owned preview fixture: unchanged source, an intentionally invalid declaration, and exact source restoration. It never terminates Xcode. Builds can change Xcode's Canvas state.

Prerequisites: the pinned Xcode frameworks installed, existing Python Frida bindings, and the selected owned project already active in Xcode. The source hash must match the original fixture. Output must be a new directory. Run from the repository root:

```sh
python3 tools/re/native-canvas-build-runtime/run.py \
  --output /private/tmp/canvas-build-fresh \
  --pid XCODE_PID \
  --workspace /absolute/repo/research/build/preview-workspaces/FIXTURE/PreviewLab.xcodeproj \
  --source /absolute/repo/research/build/preview-workspaces/FIXTURE/Sources/PreviewLab/PreviewLab.swift
python3 tools/re/native-canvas-build-runtime/verify.py /private/tmp/canvas-build-fresh
```

The exclusive controller lock covers attachment, builds, source mutation and restoration. Each AppleScript build command checks the active workspace path before building. Source replacement/restoration checks for concurrent edits; unexpected user edits are preserved. Frida stages have cancellation deadlines; AppleScript is bounded to 25 seconds per build. A pending Xcode build is not killed. If interrupted outside Python cleanup, inspect the output source backup before restoring anything.

The agent pins loaded Mach-O UUIDs and on-disk full hashes, observes existing recovered listener/handler entry points, and reads the result getter only within the stop listener call. Agent-side phase markers separate the builds. No callback arguments or return values are changed. Trace collection can affect timing; host timestamps are message reception times, not precise native durations.

The verifier checks callback order and result correlation. It is an assertion reader, not a native rerun. Native evidence and retained harness failures: [build runtime evidence](../../../research/evidence/canvas-runtime-build-notifications-2026-11-02/README.md). This test does not establish notification payload contents, build-stop refresh gates, UI rendering completion, transport cleanup or cross-platform functionality.
