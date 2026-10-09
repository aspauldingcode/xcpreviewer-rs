# Retaining approved Xcode access and rejecting blank captures

## Research result

The installed Xcode 26.6 build 17F113 prompts for the parent agent process: the fresh worker and retained broker prompts named different Python PIDs. A stable session UUID alone has not been shown to preserve approval across parent exits. [Apple's access guide](https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode) describes enabling external agents and using mcpbridge; it does not document a permanent approval bypass. Its JSON documentation was read directly because the HTML page requires JavaScript.

Installed IDEIntelligence binaries contain candidate private preferences `IDEChatInternalAllowUntrustedAgentsWithoutUserInteraction` and `IDEIntelligenceAllowApprovingUntrustedAgentsForSession`, alongside generic tool-permission flags. These are static identifiers only: their precise gate, current semantics and ability to suppress this external-agent alert are unverified. No preference was written or protection changed. Generic skip-tool-permission flags must not be assumed equivalent to external-agent admission.

The primary [xcode-mcp-proxy repository](https://github.com/jeffy-w/xcode-mcp-proxy) implements the same general persistence idea using a LaunchAgent and local HTTP endpoint. It was inspected, not installed. Our implementation needs no added dependency, global configuration or network listener.

## Implemented and measured access reuse

`tools/re/reloop/xcodebridge.py` retains one mcpbridge subprocess under one owned agent parent and session. A private Unix socket and directory (0600/0700) serialize clients. Only window listing, file glob/read and preview rendering are allowed; arbitrary tools/methods are rejected. The CLI supplies explicit start/status/stop. Stop verifies the recorded parent identity; it does not terminate Xcode. There is no automatic restart or permission bypass.

The user explicitly approved access. Accessibility-index clicks failed because the computer-use service reported changed UI state; a fresh screenshot and coordinate click successfully dismissed the current dialog. The initially short fresh-worker request timed out before approval; that failure remains sealed.

The retained-session control returns two independent local caller results using the same broker/session after one approval. A later, separate native experiment worker also uses the same recorded broker/session, without another prompt. This solves repeated approval while that connection remains alive. Broker/Xcode restart, reboot and approval persistence across either exit are unproven; the loop must report that boundary rather than promise permanent access.

Upstream MCP messages are not traced by the managed caller. The first managed control's zero message count/empty reverse-request list means unobserved, not absent traffic; the current adapter emits null with an explicit scope. Window responses remain local to avoid publishing unrelated project titles.

## Capture falsification

Using retained access, the owned project builds, source membership is verified, and RenderPreview returns three valid 640×384 PNGs. A/A PNG bytes and decoded pixels are identical; the A/B title changes 2,260 pixels. Visual inspection showed **blank white content**. The changed pixels belong to the window title, not the expected two SwiftUI text rows. This is rejected Canvas output.

The first run's legacy checks reported supports. It is retained with explicit limited acceptance; it cannot satisfy O3. A corrected run adds an independently predicted fixture-content sanity check: interior rectangle (32,96)–(608,352), excluding title bar, rounded corners and borders, must contain at least 100 opaque nonwhite pixels for this white-background text fixture. All three snapshots contain zero. Its sealed verdict is inconclusive and accepted-content readiness is false. Positive ink alone would still require semantic confirmation; it is a necessary blank-output guard, not OCR or full conformance.

The planner now rejects chrome-only readiness and avoids generating repeatability proposals from legacy captures without content evidence. Published [rejected fixtures](../../tools/re/fixtures/CanvasBlankOracle/manifest.json) preserve the failure. All 92 tests pass, including persistent owned bridge reuse, tool restrictions, private endpoint validation and chrome-only rejection. See [sanitized runs and anchors](../../research/evidence/xcode-retained-access-2026-10-09.json).

## Next control

Reuse the live broker, not a fresh bridge per wake. Diagnose the blank owned view through a changed fixture or independent observation, distinguishing macOS window chrome from the view content. O2/O3 and both milestones remain open. Native instrumentation readiness, correlated XPC envelopes and resource completion still require their own evidence.
