# Explicit frame availability in the owned MCP prototype

The owned handler version is now 0.2.0. `preview_frame` advertises a strict object
outputSchema and returns structuredContent with `available` and `frame`.
An unavailable frame is `{"available":false,"frame":null}`; an available frame
contains its descriptor and one base64 allocation. Brief text says "Frame
available." or "No frame available.". Consumers must read structuredContent;
version 0.1 text-JSON frame consumers require migration. The MCP protocol remains
2025-11-25. This version is an owned reconstruction API, not recovered Canvas wire.

Discovery now describes startup diagnostics, retained older frames after rejected
edits, initial/post-close unavailability and restart requiring a new session.
`preview_frame_contract.js` supplies a reusable bounded decoder: exact fields,
safe revision/generation, explicit finite geometry/format/extent, canonical base64,
full allocation SHA-256 and a detached allocation/descriptor. The present consumer
uses a 64-byte row stride and therefore supports width 1–16 and height 1–64; the
broader frontend's theoretical geometry is not advertised as this API's support.

Two actual owned servers were exercised by the already-pinned official MCP
client 2.3.1 and its default Node AJV output validator. Both returned unavailable
before start. The first compiled 13×7→11×6→13×7, rejected unsupported source with
actual CLI wait 2 while retaining the older frame, recovered, closed, reported
unavailability and rejected restart. The second compiled one frame and closed
through actual SDK transport EOF. Both Node servers returned actual wait 0 through
the owned pass-through supervisor, with zero recorded workers/timers and no final
frame. Four fresh Rust modules and four independent V8 instantiations match
81,920 complete consumer bytes, including padding and unused tails.

The independent reader checks 19 correlated responses against the pinned official
JSON-RPC/initialize/tool-list/tool-result schemas, and checks frame output schemas
with Python Draft202012Validator. Receipt files and frozen source snapshots agree
with build records. Every response stays under the existing 32,768-byte cap.
Synthetic frame controls additionally compare 16,384 exact arithmetic bytes and
replay in two fresh Node processes. Eight malformed/inconsistent frames fail the
reusable decoder; the official SDK AJV and independent Python schema both reject
six structural faults while accepting the geometry-product and digest-value
faults. These two values need semantic/full-byte validation beyond JSON Schema.
Three resealed availability, actual-wait and correlated padding faults fail the
independent evidence reader. The isolated archive passes 89 Python plus 7 Rust tests.

One failed owned experiment is retained: duplicating the complete allocation in
text and structuredContent exceeded the unchanged reply cap and produced the
generic tool error. The fix retains one typed allocation and brief text, without
increasing any cap or deadline. A verifier test initially expected AssertionError
when jsonschema raised ValidationError for the deliberately broken availability;
that rejection was correct. The reader now reports a concise contract assertion,
without dumping allocations. No native rerun was needed for that harness repair.
A dictionary-shaped graph-state preflight was corrected before mutation.

Evidence: `research/evidence/mcp-frame-contract-2026-10-11/manifest.json`, SHA-256
`12f27a051a37998f49d04c8dd50accaaaf3210f68deacfbf9ec14ba91359b711`.

Next: exercise first-build rejection and recovery, retained diagnostics versus
current availability, and refresh/reset behavior through independently reviewed
user workflow controls. Modern protocol negotiation, broader source compatibility,
packaging/platform acceptance and actual native Canvas transport remain open.
The approved private Xcode bridge is still offline and was not restarted.
Both milestones remain open.
