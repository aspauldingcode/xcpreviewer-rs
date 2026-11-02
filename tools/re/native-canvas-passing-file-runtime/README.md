# Passing modified-file runtime control

This macOS/arm64 test extends the existing owned fixture temporarily with a second Swift target member, without opening it in an editor. It builds the target, waits beyond the recovered timestamp gate, modifies the new file's constant and restores its value. It observes native selection, coalescer and scene-update method execution. The fixture member is deliberately not referenced by the preview, so no changed rendered output is expected or asserted.

Prerequisites and pinned image restrictions match the [file timing controls](../native-canvas-file-runtime/README.md). Run from repository root with the owned project already active in Xcode:

```sh
python3 tools/re/native-canvas-passing-file-runtime/run.py \
  --output /private/tmp/canvas-passing-file-fresh \
  --pid XCODE_PID \
  --workspace /absolute/repo/research/build/preview-workspaces/FIXTURE/PreviewLab.xcodeproj \
  --source /absolute/repo/research/build/preview-workspaces/FIXTURE/Sources/PreviewLab/PreviewLab.swift
python3 tools/re/native-canvas-passing-file-runtime/verify.py /private/tmp/canvas-passing-file-fresh
```

Output must be new. Original primary source and project digests are mandatory; the extra filename must not exist. The exclusive controller lock covers setup, attachment, build, edits and teardown. The build checks active workspace identity. Frida stages and AppleScript builds have bounded deadlines. Source/project backups are retained locally. Cleanup restores project bytes and deletes only the test-created file when current bytes still match the harness's expected contents; concurrent changes are preserved. Interruptions outside finally cleanup require inspecting the backups and current files before restoring anything. Xcode is never terminated.

The observational agent reuses previously recovered function/block locations. It resolves the existing WorkspaceScene.setNeedsUpdate export and logs entry/return under the active workspace-handler invocation. Caller offsets tie the coalescer and scene method calls to the recovered modified-file route. No synthetic notifications, forced predicate results, preference changes or timestamps are used.

The build receipt includes a Boolean indicating whether the completed build log contains the new filename. Raw build log text is not published. The verifier requires actual native non-thunkable/should-update results, matching coalescer/scene entries, method return, handler return, file/project restoration and detach. The added member is not an exercised preview dependency: rendered refresh, state continuity and native resource settlement remain open. See [executed evidence](../../../research/evidence/canvas-runtime-passing-file-2026-11-02/README.md).
