# Real build listener execution: success, failure and recovery

Static expansion remains paused. Two serial native runs each completed three actual Xcode builds against the same owned project. These are running shipped-code observations, not interpreted source or a simulated event replay. The second run used agent-side phase markers and a reusable parameterized runner.

| Actual control | AppleScript completed/status | isPreviewsBuild getter inside start listener | result getter inside stop listener |
| --- | --- | --- | --- |
| Original source build | true / succeeded | 0 | 1 |
| Real source edit appends an invalid declaration; build | true / failed | 0 | 2 |
| Exact source restoration; build | true / succeeded | 0 | 1 |

All six completed builds exercised the recovered start listener, isPreviewsBuild getter, workspace handler, stop listener, result getter and a later workspace handler entry, in that observed order. Additional workspace-handler entries occurred; they are not attributed to a particular payload. All selected callbacks ran on thread 259 in these samples. No preview-build (`isPreviewsBuild == 1`) control was exercised. Result values correlate with actual action statuses in these runs; no universal enum/version mapping is claimed.

## Executed interfaces and provenance

Existing source evidence: [listener classification](../canvas-build-listener-2026-11-01/README.md), [build-stop gates](../canvas-build-stop-2026-11-01/README.md). No additional broad function discovery was performed. The installed Xcode.sdef supplied the public AppleScript `build` command and scheme-action `completed`/`status` interfaces, allowing builds while Xcode's native window was not exposed on the current Space.

Pinned loaded PreviewsXcode UUID `25c99c664185307188e31ab474573a10`, full file SHA-256 `ed08ea2f7e077fc0aeeecfd089e0901acb666a35bff3ef8610f8bf719cea424b`; listener offsets 0x16ed0c/0x16ef1c and workspace handler 0x248ef0. PreviewsIDEAPI UUID `b8c195f9db4837999653d7aa8bcb986e`, SHA-256 `d3e0ad14a4ea159fde12482d92fb7b7d3f86e4df1578fcef76961a294fbe71f0`; getter offset 0x8fb0. The public Objective-C runtime resolves IDEBuildOperation's result implementation; only calls nested within the stop listener are logged. Offsets/UUIDs and original instrumentation are published; no Apple instruction dumps or binaries are included.

`initial/` and `reproduced/` retain the exact executed original runners/agents, AppleScript commands, JSONL messages and three action receipts each. `assertions.json` contains verifier results and four rejected recorded-trace mutations (missing stop, wrong result, wrong phase, false restoration). Those mutations validate assertions; they are not additional native controls. `verify.py` checks captured ordering, matching action receipts, single selected listener/getter calls per action window, thread correlation, completion and cleanup receipts. Reproduce with tools/re/native-canvas-build-runtime; output must be new and the owned project already active.

## Failure and cleanup evidence

The earlier identity probe incorrectly passed an integer to Frida's get_process name API and failed before attachment; retained as a harness failure. A corrected first capture attached and observed start/handler but its fixed capture window expired before stop. That partial capture does not verify completion. `retained-failures.json` preserves both. A native UI activation attempt still exposed Cursor rather than a targetable Xcode window; no blind menu action was issued. The AppleScript route then verified the exact active owned workspace and executed the builds without requiring a visible window.

The exclusive controller lock covered each native run. Frida stages and AppleScript builds were bounded; the second run also bounded unload/detach. Each run's finally receipt records exact source restoration and detach without target termination. The independent post-run check found Xcode PID 5841 still running at /Applications/Xcode.app/Contents/MacOS/Xcode and the controller lock available. Source SHA-256 returned to `128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef`. The owned file-error source was `d12b6d12e602b02e05d326c0ffd5d9173162783dfa046f87d6e1de71c738631c`. No user edits were overwritten in these runs.

## Evidence limits

Native listener/handler **entry execution** and nested getter results are exercised. NotificationCenter posting names, actual subscriber payload tags, workspace mismatch rejection, timestamp suppression boundary, build-stop preference/state gates, cache invalidation, setNeedsUpdate, private Preview.update, rendered completion and transport/render resource release remain unverified here. Hooks do not read or alter notification payloads. No raw observer pointer lifetimes were inferred from process-local result receiver identifiers. Agent overhead and host message timestamps do not establish native timing guarantees. The failed source build is an intended failure control; it does not prove last-good-preview retention or UI error presentation.

Earlier native observer component and rendered-file-change controls remain separately scoped; they were not rerun in this package. No Rust product changes or Rust tests occurred. This adds runtime evidence on one native project/profile, not working standalone WASM SwiftUI, all-device coverage or full-area acceptance. Full native recovery stays 0/9; tracked delivery stays 1/26 (3.8%).
