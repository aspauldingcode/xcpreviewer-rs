# Native build-stop loaded-false preference route

Static expansion remains paused. Two qualified native runs each executed actual success → source-error failure → exact-restoration recovery builds in the owned macOS fixture. All six completed stop handlers observed the loaded auto-resume Bool as false. Stop success payloads were **1, 0, 1**, matching result getter reads **1, 2, 1** and actual AppleScript succeeded/failed/succeeded statuses.

Each qualified stop-handler trace was: workspace-handler entry → build-stop preference inputs → shared return path → handler return. No scene gate, building-state inspection, coalescer or scene-update entry occurred within those six stop invocations. Build-start invocations separately can traverse scene/coalescer paths; they are not confused with stop invocations. No preference was changed and no private notification or handler was directly invoked.

This qualifies the existing recovered **false loaded-input path**. It does not identify a persisted preference key/value, a factory default, the UI setting, or a true-input result. The failed build's payload was observed false, but both loaded preference and payload were false in that case; this is not an isolated true-preference/failed-payload control.

## Native qualification and assertions

Source anchor: [existing build-stop gate evidence](../canvas-build-stop-2026-11-01/README.md). Same pinned PreviewsXcode/PreviewsIDEAPI hashes and loaded UUIDs as [real build listener controls](../canvas-runtime-build-notifications-2026-11-02/README.md). No new functions or broad static discovery were added. At the already qualified 0x2496d8, native code loads the generic Bool output into w8; 0x2496dc ANDs it with w27's payload. A single observational probe at 0x2496dc reads x8/x27 low bits before that instruction. The known following TBZ at 0x2496e0 targets 0x24a088; this shared return block is attributed only within the same enclosing handler invocation. The source semantics name the register values; the trace establishes that this instruction path actually executed.

Existing scene gate 0x249704 and native building-state tag point 0x24974c are instrumented, as are the previous coalescer/scene method entries. Their absence is bounded to the selected, fully returned handler invocations under successfully loaded hooks. No preference state, register value, return value or branch outcome was forced. Instrumentation affects timing.

single-probe/ and reproduced/ retain exact original executed drivers/agents, AppleScript commands, messages and action receipts. verify.py checks complete real action windows, native result/payload correlation, phase/thread/invocation ordering, the false input, return path, no downstream entries in that handler, source restoration and detach. Both runs pass. Seven corrected recorded-trace mutations reject: preference, payload, return path, handler return, unexpected scene gate, phase and restoration. They test assertions and are not seven additional native executions. The verifier intentionally rejects a true preference input rather than claiming that environment was exercised.

## Preserved failures and route change

The first native capture used adjacent probes at 0x2496dc and 0x2496e0. Three real builds completed and the latter reported a zero combined value, but expected preference-input reports were missing. That capture **fails** the gate verifier and remains under incomplete-adjacent-probes/. Removing the adjacent probe produced complete input reports in both later runs. The underlying reason for the initial reporting gap was not established; no Apple behavior or exact instrumentation-interference cause is inferred.

The first missing-return trace mutation accidentally removed build-start invocation 1's shared return rather than stop invocation 2's. The verifier correctly accepted the still-complete stop trace, causing the mutation builder's expected rejection assertion to fail. The corrected builder selects by stop invocation ID and rejects. mutation-construction-failure.json records that harness mistake; it is not a native failure.

A native UI observation returned `Xcode has no accessible window (not drawn yet?)`. ui-access-limitation.json transcribes the structured tool failure. No repeated activation, blind keyboard/menu action or browser route was used to manufacture a rendered-output check. Work switched to existing native build-stop gates; native rendered completion remains unverified.

## Cleanup and remaining scope

Exclusive controller lock covered each build/instrumentation session. Active-workspace checks and bounded Frida/AppleScript stages applied. All three captures restored exact source bytes and detached without terminating user Xcode. Independent cleanup found controller available, PID 5841 still running at /Applications/Xcode.app/Contents/MacOS/Xcode, and source SHA-256 `128a57d8195466a929a95c91658e4b4dbd5ac7d731303e982639fbaa7b5c39ef`. The UI observation was read-only; no system protection, signing or preference change occurred. No native crash occurred.

Unknown: true-preference branch, missing/present scene gates and all four native building-state controls, accepted refresh payload, asynchronous resume/queue completion, private Preview.update, rendered result, persistent SwiftUI state, native resource release and other targets/hosts. The earlier positive passing-file route is separate evidence, not evidence that build-stop auto-resume completed. No Rust product changes or Rust tests. No Apple instruction dump or binary is published. Full native areas stay 0/9; issue-based tracked delivery stays 1/26 (3.8%).
