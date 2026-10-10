# Anchored source WASM in an actual browser and Canvas2D

Four previously sealed owned literal-source modules execute in the actual Codex in-app browser using WebAssembly.compile/instantiate, with no imports. Two sealed campaigns each run two fresh page loads. Each load renders unchanged red/red/blue/padded fixtures, reads the complete204800-byte allocation after rendering and after each of four invalid strides per module, then copies active pixels into Canvas2D and reads them back with getImageData. Browser DOM observations explicitly show four completed modules and16 invalid requests per load. This is browser execution, rather than another Node.js V8 experiment.

Across both campaigns, independent comparisons cover3,276,800 baseline allocation bytes,13,107,200 invalid-request allocation bytes and2,457,696 Canvas2D RGBA bytes. The expected prefix comes from the anchored prior source corpus whose red/blue active frames already match native ImageRenderer and whose small padded fixture matches independent literals. Allocation tails must remain0xa5; rendered row padding must remain0xcd. Each invalid request's entire allocation is compared immediately, so later restoration cannot hide an intermediate mutation. Canvas readback compares opaque active pixels without row padding. Repeat payloads are exactly equal.

## Tool and ownership boundary

The browser runner is an owned HTML page, served on an ephemeral127.0.0.1 port by a bounded adapter under the exclusive controller lock. Only that page and four owned WASM modules are served. Reports have a per-run nonce, exact repeat index and8MiB bound; invalid identity/module/import/geometry/content reports fail. The server has a120-second deadline, closes its socket and stops its thread in finally. Both temporary agent-created browser tabs are explicitly closed before finishing; no Xcode windows or user processes are touched. Browser operations use the existing approved computer-use tool; no Safari automation settings or system protections change.

User-agent reports Chrome155 on Macintosh. This does not independently pin the browser binary, engine architecture or operating-system version. Host context is the current macOS desktop; there is no Windows browser or general browser-engine coverage claim. Runtime reported checks are corroborated by actual page navigation/completion observations; sealed data verifies artifact integrity, not universal browser provenance.

## Retained failure and checks

The first campaign fails before serving because the controller source inventory omitted HTML, leaving the browser template absent from its frozen source tree. Including HTML in the reviewed source inventory repairs it. That failed seal is retained alongside both accepted seals in [sanitized evidence](../../research/evidence/browser-source-wasm-2026-10-10.json). The initial accepted acquisition used a surface adapter flag; final routing correctly uses the portable adapter and rejects ignored source/interpreter flags. Both accepted campaigns execute identical anchored module bytes.

Four new verifier tests reject stale/non-typed identity, wrong module/import/geometry, Canvas corruption, pixel/padding/tail faults and intermediate invalid-request mutation; they also require the HTML template to be frozen and enforce exclusive browser mode. All247 repository tests pass.

## Acceptance and next work

The narrow actual browser execution/readback feasibility boundary passes. F2 and both delivery milestones remain open: source compilation still occurs on macOS, and this is an explicit opaque red/blue literal subset rather than general SwiftUI, hot reload, Xcode transport, arbitrary alpha/color management or performance qualification. The work graph marks this research task complete without accepting the F2 issue. Next independent task expands native alpha/compositing oracle coverage while native correlated capture and typed continuation tracks retain their changed-prerequisite blockers.
