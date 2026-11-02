# Native workspace events invalidate builder cache

This source unit classifies the six payload-free XcodeWorkspaceListener.Event cases in the pinned shipped Xcode image. It connects event handling to the previously recovered coalescer and builder reuse policy. No runtime event was sent or observed.

| Event | Coalescer/cache action | Scene reason |
| --- | --- | --- |
| workspaceSettingsChanged | setNeedsUpdate; clear/release lastWorkspaceBuilder | workspaceChanged, Workspace build settings changed |
| newSchemeSelected | same | workspaceChanged, Current scheme changed |
| newRunDestinationSelected | same | previewsChanged |
| didFinishPackageLoading | same | workspaceChanged, Current scheme changed |
| activeSchemeDidChange | same | workspaceChanged, Current scheme changed |
| installablePlatformsDidChange | same | workspaceChanged, Current scheme changed |

The repeated Current scheme changed text is the recovered native reason text; it is not a claim that each event semantically represents a scheme switch. Two cases share one handler entry. Each route requests WorkspaceScene.setNeedsUpdate when the optional scene exists. Every route schedules the environment coalescer and clears/releases the last builder before this optional scene branch.

The reader validates the field descriptor kind/record size/count, nominal enum payload/empty case counts (5/6), associated-type presence, eleven reflected names and the actual enum-tag witness. Payload-free logical tags are the word at offset zero plus five; payload tags are byte eight for tags zero through four. A small bounded interpreter follows the native comparison/conditional-branch instructions for all six valid empty cases; entry addresses, coalescer calls and cache clear stores must match. The reader binds eight selected calls through Mach-O import/defined symbol metadata and checks native reason strings. It compares all 5,184 instruction bytes in the event handler and tag witness against the mapped file bytes. Verifying the complete byte range does not imply complete semantic recovery of every payload branch.

The five payload cases are blueprintDidChange, modifiedFiles, removedFiles, buildSystemBuildStarted and buildSystemBuildStopped. Their names are recovered but their detailed handling, notification sources and delivery timing are not classified here. Runtime preference/auto-refresh gates, dynamic cache identity, coalescing delay, cross-target transitions and full session/render/input/resource semantics remain open. Prior native UI evidence is contextual only and was not reobserved.

`verify.py` verifies original-reader pins and runs source.py from a fresh copied workspace; complete findings must agree. Raw disassembly/full binary data stay in temporary local directories. No Apple binaries or instruction dumps are included. REA server identity is aligned with no open binary session. The unchanged previous Ghidra listing limitation was not retried. No private method/guessed ABI invocation, synthetic event delivery, UI action, build/refresh, process signal, preference change, product implementation or Rust test rerun occurred. Controllers release on exit. Both milestone contracts and full Canvas recovery remain incomplete. Publication and matching GitHub issue updates are locally deferred behind the existing explicit approval gate.
