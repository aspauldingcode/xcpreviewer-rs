# Native runtime validation — 2026-11-02

Static expansion is paused. These tests execute the shipped PreviewsFoundationHost implementation in isolated owned processes. They are not source replay or a replacement model. Native UI observations separately exercise the open owned PreviewLab project.

## Demonstrated component behavior

| Executed control | Observed result |
| --- | --- |
| Register → invalidate → invalidate again | Callback once; native storage kept owned context alive after caller release; context deinit and FD closure before first invalidate returned; second invalidation silent. |
| Late registration | Callback before registration returned; no token returned. |
| Cancel twice → invalidate | No observer callback; context deinit during first cancel; no second cleanup; descriptor was closed. |
| Owner released with live token → cancel | Weak native owner and owned context cleared; FD closed; subsequent token cancel returned without callback. |
| Drop waiting token → invalidate | Dropping token did not unsubscribe; later invalidation called observer. No assertion/process termination in this control; unified diagnostics were not captured. |
| Register A/B/C, cancel B, invalidate | Callback order A then C; all three context descriptors closed. |
| Invalidate again from callback | Returned without deadlock; one callback total. |
| Invalidate from context destructor during cancel | Owned process terminated. Matching crash diagnostic: “Trying to recursively lock an os_unfair_lock.” Stack places deinit in native locked removal. This is a deliberately reentrant payload control, not a claim about ordinary application callbacks. |

Weak references and `fcntl(F_GETFD) == -1 / EBADF` assertions run in the executable. FD is an owned `/dev/null` sentinel held by observer context, not an XPC/Mach/IOSurface transport resource. Numerical retain counts and concurrent race behavior were not measured. The handle fixture explicitly selects `softAssertDebugOnly`; token construction uses the shipped constructor. All results are scoped to pinned arm64 PreviewsFoundationHost UUID `6b75229bde5d3d3794bc75af4f4704c6` and SHA in the runner. This does not qualify all Canvas targets or standalone WASM.

## Reproduce

From repository root:

```sh
python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-new-run
python3 tools/re/native-canvas-runtime/run.py --output /private/tmp/canvas-native-negative-run --include-negative-control
```

Output directory must be new. Compilers have 30-second deadlines; owned native cases have eight-second deadlines and private process-group cleanup. Exclusive controller lock prevents competing native experiments. Negative control intentionally terminates only its owned child. Match its PID to a sanitized macOS crash report before classifying the failure. `verify.py` checks executed traces and assertions; it never accepts disassembly replay as native evidence.

## Native Xcode/file controls

The UI procedure is reproducible against the owned fixture using `ui-session.py` (title edit), `ui-body-session.py` (visible text edit), and `ui-failure-session.py` (intentional syntax error). Each holds controller lock for at most 240 seconds, backs up exact source bytes, accepts `ui-edit`, `ui-restore`, `ui-stop` command files in its stated directory, and conditionally restores without overwriting concurrent edits. The current fixture path is explicit in these scripts; use an owned copy, never arbitrary user source. Native AX actions/snapshots and screenshots are retained alongside source-change hashes.

1. Observe baseline PreviewLab window; start session and request edit.
2. Observe title change. Product → Build was invoked through AX menu; subsequent tree reported “Build Succeeded” and “Canvas paused.”
3. Restore source and refresh Canvas. Body session changes selected preview text to “Runtime pixels A”; screenshot shows that rendered text, not just an editor change.
4. Restore. Failure session appends invalid type syntax. Native UI reports “Cannot preview in this file” and expected-type diagnostic; screenshot shows blank preview. Build menu was disabled for the attempted failure build, so no failed-build notification claim is made.
5. Restore exact original source. Screenshot shows original “Layout baseline” preview rendered again; original source SHA is checked.

Internal IDEBuildOperation notifications and recovered private refresh functions were **not traced**. Frida attachment was cancelled at four seconds before hooks installed. UI build success is not verification of those notification callbacks or of exact refresh timing gates. Syntax-error activity retained an earlier Build Succeeded label; it was not counted as a new build success. UI tests are recorded manual/AX procedures, not an unattended end-to-end UI runner.

## Evidence levels and remaining unknowns

- `static-audit.json`: 25 existing static-only Canvas evidence bundles. Replay does not upgrade them.
- `coverage.json`: distinguishes static reconstruction, simulated branch replay, native component execution, native UI observation and working product scope.
- `native-*.stdout`: ordered JSONL execution traces; `*.result.json`: actual process outcomes; native Swift preconditions test lifetimes/FD closure.
- `cancel-reentry-crash.json`: sanitized report matched to owned failing PID. No raw Apple dump is published.
- UI JSON, screen hashes and JPGs: real owned-project file update, successful UI build, syntax error and recovery.
- `failures/`: original compile syntax failure and two invalid ABI harness attempts. Initial empty-trace call used wrong direct-result convention and corrupted owned process state. Correcting its indirect result produced the passing controls. These crashes are harness failures, not native Canvas bugs.
- LLDB target creation exceeded its twelve-second bound. Frida attach timed out. Python cache write and initial mixed-schema audit packaging failures were corrected without altering native outcomes.

Still unknown: internal build notifications; exact private Preview.update/reconciliation execution; full refresh debounce/state preservation; transport/rendering resource settlement; all target/version profiles; standalone WASM UI/runtime. Existing reconstruction has not become a working cross-platform Canvas because these component tests pass. Full native acceptance remains 0/9 areas, overall tracked delivery 1/26 (3.8%).
