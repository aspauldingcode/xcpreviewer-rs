# Progress

## Branches

- `master`: original roadmap and verified research milestones.
- `development`: active investigation and implementation.

## 2026-10-08 — first reverse engineering pass

Completed:

- Established and pushed `master` and `development` to the requested GitHub repository.
- Inventoried 18 Xcode preview binaries/archives and 8 OS SDK stubs.
- Recorded hashes, UUIDs, load commands, symbols, demangled Swift signatures, and strings locally.
- Built runtime metadata dumper; inspected OS and host frameworks in separate processes.
- Identified `UVPropertyList` and XPC coding adapters.
- Verified synthetic binary-plist serialization and native message-key getters.
- Recovered bitmap, render, layer-host, launch, stream identity, and JIT loading interfaces.
- Added reproducible collection, disassembly, runtime dump, and Ghidra scripts.
- Decompiled seven selected functions in Ghidra and saved the local project. Full automatic analysis hit its 120-second limit; selected function decompilations succeeded.
- Verified all collection commands, isolated runtime loads, native getter results, and independent Python binary-plist decoding.

Next:

- Trace a minimal native macOS preview session and capture message envelopes.
- Recover exact raw discriminants, replies, version negotiation, and surface transfer.
- Define a separately named portable protocol only after identifying the required semantics.

Not yet implemented: Rust preview core, SwiftUI compatibility layer, WASM compilation/runtime, renderer, bindings, or portable preview MCP server. The research-tool MCP server is implemented in the subsequent milestone. Nothing in this milestone establishes end-to-end preview compatibility.

## 2026-10-08 — free agentic RE toolkit

Implemented:

- Bounded serial executor with a reviewed eight-experiment queue, strict adapter validation, dependency selection and exclusive ownership.
- Frozen worker source copies, per-run manifests/journals, SHA-256 verification, atomic checkpoints, interruption recovery, time/artifact budgets and owned-process cleanup.
- Local stdio MCP server exposing discovery, status, ready work, bounded execution, proposal validation, evidence verification and report candidates.
- GhidraVibe service management, schema discovery, engine health checks, optional stdio bridge and reviewed read-tool allowlist; isolated direct headless analysis remains available.
- Frida 17 tracing of six owned native calls and six synthetic `UVPropertyList` outputs; independent payload decoding verifies values with zero script errors.
- LLDB tracing of six owned calls with matching arguments and loaded-image identities.
- SwiftUI native reference capture, PNG differential checking and a data-preserving plist decoder.
- Free pinned Python dependencies installed locally; no paid analysis API required.
- Xcode's installed MCP bridge discovery helper. Discovery reports no running Xcode instance on this machine; no settings were changed.
- Full [loop design](docs/reverse-engineering/agentic-loop.md), [operator prompt](docs/reverse-engineering/agentic-loop-prompt.md) and [tool/setup matrix](docs/reverse-engineering/toolkit.md).

Validation: 19 automated tests pass. Real-tool validation includes the native debugger, Frida hook/payload capture, SwiftUI PNG rendering, collection/runtime/disassembly, healthy GhidraVibe engine with 70 advertised tools, real HTTP dyld-cache discovery and stdio MCP bridge calls, and two selected saved Ghidra decompilations. Full Ghidra automatic analysis remains partial at its configured 120-second limit. All eight seeded experiments passed and all sealed artifact hashes verified; see the [toolkit evidence index](research/evidence/agentic-toolkit-2026-10-08.json).

Next: open an owned fixture in Xcode, discover its enabled MCP preview tools, then capture one actual canvas lifecycle with correlated request/reply and output resources. The existing synthetic trace and ImageRenderer reference do not establish a live wire protocol. XPC attachment lifetimes, replay, portable SwiftUI/WASM and the Rust renderer remain open.

## 2026-10-08 — connected analysis and exact verification

Implemented:

- Live schema-driven Ghidra program queries and repository-owned import/function preparation; six Frida events joined by image hash, Mach-O UUID and function offset to decompilation/disassembly/references.
- Bounded static Swift nominal/field metadata reader: 351 types and 998 fields on the pinned image; unresolved symbolic/indirect references remain unknown.
- Typed differential plist corpus, exact streaming byte/bit comparisons, cross-process repeatability checks and deterministic semantic failure shrinking.
- Three small synthetic native goldens with original inputs, Apple reference bytes, hashes, probe provenance and a sealed-run manifest anchor.
- Evidence SQLite/FTS index and graph, exact artifact/response paging, scoped claims, and reviewed counterexperiment templates. MCP now exposes 19 tools; large responses retain full local originals.
- External manifest anchor verification, changed-input detection, frozen-source verification and comparison-time integrity checks. Self-consistency alone is explicitly not authentication.
- Owned macOS Xcode project and real canvas adapter with exact project selection, source/build preflight, controlled variants and mapping-verified late instrumentation. Mutable Xcode workspaces stay outside frozen sources and sealed artifacts.

Validation: 40 automated tests pass. Native connected/static experiments pass. Seed seven passes 24 cases; reviewed seed-eight follow-up passes 32 cases. In each campaign, repeated calls, fresh objects, Foundation encoding and a second helper process produce identical Apple bytes for every case; independent Python decoding preserves typed values. Python encoding matches Apple in only six cases per campaign, so semantic round trips do not establish encoder byte compatibility. System `cmp` checks a published native golden, and MCP comparison rejects a 49-byte Unicode encoding difference.

Canvas status: the owned native project builds successfully after disabling its stalled SDK stat-cache optimization. Xcode MCP then times out on `tools/list`. Earlier attempts exposed source-group lookup and active-scheme issues. No real canvas snapshot or complete correlated IPC capture is claimed. The verifier also detected Xcode updating workspace UI state after sealing and quarantined that run. The final adapter moves active workspaces outside sealed artifacts; isolation is unit-tested. Preserve diagnostics; diagnose bridge responsiveness before another expensive render attempt. The controller recommends diagnosis rather than unchanged retries.

See the [machine-readable evidence and manifest anchors](research/evidence/connected-verification-2026-10-08.json), [golden fixtures](tools/re/fixtures/PlistOracle/manifest.json), and [verification/edge-case/porting contract](docs/reverse-engineering/verification.md). All successful measurements retain their exact frozen tool versions locally. Raw Apple binaries, full decompilation, private metadata and active Xcode workspace state are excluded from publication.

Next: restore reliable Xcode MCP schema responses, obtain A/A and controlled A/B canvas captures, then recover a complete transport envelope and attachment lifecycle before implementing replay or claiming portable preview compatibility.

## 2026-10-08 — recursive XPC boundary recovery

Four new sealed experiments pass: 32 local XPC dictionary round trips with exact payload/property-data and cross-process byte equality; malformed-envelope controls; all 105 prefixes of a 104-byte Unicode plist; and ten statically recovered message raw strings corroborated against Swift metadata. A cross-adapter comparison matches the prior published Unicode oracle byte for byte, with zero differing bits.

Nonempty truncated native data decodes as an empty dictionary; missing/wrong-type/empty XPC fields return nil. Direct empty NSData also decodes empty. Shrinking reduces the fallback reproducer to one input key. A published eight-byte synthetic malformed golden preserves the native/strict-Python decoder difference.

The serial controller now has 16 adapters and 19 MCP tools. All 52 automated tests pass; all four final runs retain verified artifacts and frozen sources. Earlier harness failures remain sealed and inconclusive. Evidence indexing and scoped claims consume the final runs; the planner follows observed failures without duplicating queued work.

Three bounded bridge diagnostics still time out on Xcode MCP tools/list after successful initialization, including with the owned project open and a fresh pinned session. No real canvas image, live wire envelope or resource-transfer compatibility is claimed. Continue with a responsive capture path and live validation of the static strings, then recover attachments and lifecycle semantics.

See [findings and limits](docs/reverse-engineering/2026-10-08-xpc-boundary.md), [manifest anchors](research/evidence/xpc-boundary-2026-10-08.json) and [synthetic malformed golden](tools/re/fixtures/XPCOracle/manifest.json).

## 2026-10-08 — raw coder and surface reference loop

Three final sealed experiments pass. Raw XPC coding repeats 28 controls in fresh processes: key arguments are ignored, a fixed data slot is overwritten by the last write, requested decoding classes are not enforced for the nonempty NSData controls, and non-data objects raise encoding exceptions. The malformed wrapper boundary now has a directly measured underlying coder contract.

Four owned single-plane BGRA surfaces preserve exact CPU bytes, including padded rows, through local XPC holder/original/lookup-reference release. Aliases share a one-byte mutation; all snapshots repeat across fresh processes. Published 3×2 surface goldens include 128-byte stride, native bytes, hashes and sealed provenance. Cross-process resource transfer and GPU synchronization remain untested.

Native UI Refresh builds and launches owned PreviewLab, but canvas content stays blank. Mapping-verified native attach stalls; a revised ten-second cancellable control stops before session creation. Frida operations now have cancellation bounds and phase diagnostics, partial-session cleanup is retained, and loader notifications defer hook installation. The revised hook captures six exact synthetic payloads on an owned helper. Its first readiness handshake failure remains sealed; fixture ordering was corrected.

All 62 automated tests pass. Controller: 19 adapters, 19 MCP tools. Final evidence hashes/frozen sources verify; scoped claims indexed. See [findings and next experiments](docs/reverse-engineering/2026-10-08-raw-coder-surface.md), [evidence anchors](research/evidence/raw-coder-surface-2026-10-08.json) and [surface goldens](tools/re/fixtures/SurfaceOracle/manifest.json). No live wire envelope, accepted canvas pixels, interprocess resource oracle or portable renderer is claimed.

## 2026-10-09 — owned process-boundary surface handoff

One final sealed experiment passes eight cases, each repeated with fresh sender/receiver peers: four CPU BGRA shapes under clean and abrupt sender exits. Real Mach surface-right transfer, kernel audit PID checks, shared mutation, received-right deallocation, actual sender wait status and retained receiver bytes are verified. All three snapshot stages match independent byte expectations, including row padding. Temporary rendezvous disappearance is required for success.

Published 3×2 handoff goldens retain 256 bytes per stage. Initial and post-sender-exit bytes exactly match the prior local-reference native goldens; system cmp independently confirms both. The second receiver mutation produces the prescribed two-byte/eight-bit change from initial bytes.

The first sealed run remains inconclusive: explicit unregister failed after byte checks. The corrected helper destroys the receive right and verifies name disappearance. An earlier manual inherited-port route timed out; its cause remains unknown. Deprecated bootstrap registration is a local research dependency, not a portable transport implementation.

All 67 automated tests pass. Controller: 20 adapters, 19 MCP tools. Final artifacts and frozen sources verify, scoped claim indexed. See [findings and limits](docs/reverse-engineering/2026-10-09-surface-ipc.md), [manifest anchors](research/evidence/surface-ipc-2026-10-09.json), and [native handoff goldens](tools/re/fixtures/SurfaceIPCOracle/manifest.json).

Next: receiver-first exit, explicit reuse/completion identity and release accounting. GPU fences, multi-plane formats, actual canvas XPC envelope and portable preview compatibility remain unverified. No Xcode or simulator settings changed in this campaign.

## 2026-10-09 — remaining-work plan and GitHub milestones

Published an evidence-based [remaining-work plan](docs/remaining-work.md), with dependencies, deliverables and acceptance gates for native capture, protocol/resource recovery, portable compiler/runtime feasibility, Rust/WASM implementation, transactional hot reload, developer canvas, independent conformance, cost/latency qualification and platform packaging.

GitHub tracking now contains two open milestones: [0 → Reverse-engineered](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/1), with nine remaining issues and one completed toolkit baseline; and [Reverse-engineered → Fully cross-platform WASM canvas](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/2), with sixteen remaining issues. The [stable roadmap mapping](research/roadmap/github.json) retains remote IDs and planning dependencies; live completion state belongs to GitHub. Conditional dependencies remain qualified in the plan and issue text.

This checkpoint adds planning and synchronization, not new native measurements. The baseline remains 20 adapters, 19 research MCP tools and 67 passing tests at implementation checkpoint `3e91d33`. Full native protocol coverage, portable SwiftUI execution and lower-cost rendering remain unproven; both milestones require their explicit evidence gates before closure.

## 2026-10-09 — receiver-first exit and local right accounting

A sealed receiver-first campaign passes eight cases, each repeated with fresh audit-verified owned peers: four CPU BGRA shapes under clean and controlled abrupt exit. Four snapshots per invocation preserve exact bytes and row padding. Parent mutation remains usable after receiver exit; the retained Mach right provides the same bytes after the original parent CF reference is released. Local parent send-right references measure 1 at creation, after copy-send and after peer exit, then 0 after explicit release. Clean receivers release imported rights and CF aliases explicitly; abrupt receivers leave them to process teardown.

The original eight sender-first cases also pass again. Four published 256-byte receiver-first snapshots exactly match their respective prior sender-first goldens, independently confirmed by system cmp. All 72 automated tests pass. Controller remains 20 adapters and 19 MCP tools; both sealed runs verify artifact hashes and frozen sources. Scoped evidence is indexed and the planner distinguishes receiver-first coverage from remaining failure/timeout work.

See [findings and next controls](docs/reverse-engineering/2026-10-09-surface-receiver.md), [evidence anchors](research/evidence/surface-receiver-2026-10-09.json), and [small native goldens](tools/re/fixtures/SurfaceReceiverOracle/manifest.json). [R1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/5) remains open: failure/timeout release accounting and final kernel reclamation are unverified. Local right counts do not establish global references or reclamation. No live Canvas XPC envelope, GPU fence or portable SwiftUI execution is claimed.

## 2026-10-09 — recurring agent-driven RE

The user authorized continuous work without repeated prompts. Created and verified active desktop heartbeat `continuous-xcode-preview-re`, returning to this chat every ten minutes. Its saved prompt requires substantive implementation/experiments, multiple useful dependent steps, evidence verification, adaptive track switching, durable checkpoints and authorized GitHub synchronization. Caveman FULL remains active for user-facing updates.

The [runbook](docs/reverse-engineering/continuous-loop.md) and [compact checkpoint](research/loop/continuous.json) preserve next actions and stop conditions outside conversational memory. Existing native deadlines and exclusive controller ownership remain in force. Unchanged failures require a changed prerequisite; fully blocked wakes perform cheap state checks. Notifications are reserved for meaningful progress, new failures, required input or completion. The loop pauses on verified milestone-one achievement or user request. Local execution requires the computer and desktop app running and remains subject to account limits and existing permissions. This setup adds scheduling, not a new native measurement.

## 2026-10-09 — recurring fault-cleanup and use-state campaign

First scheduled wake implemented a native fault helper, a reviewed `surface_failure` adapter and falsifying verifier tests. Twelve cases (four CPU BGRA shapes × closed endpoint, post-import error, pre-completion timeout) each repeat twice; exact retained/imported bytes and padding match independent predictions. Expected native error codes, actual child exits/signals, local resource/peer name disappearance and rendezvous removal are checked. Timeout termination applies only to the probe's owned child. Success-shaped output cannot override a nonzero helper exit or rejected completion.

A dependent use-state control passes four shapes, each repeated twice: local explicit counts 0/0/1/1/0 differ from global in-use false/true/true/true/false across CF-only, Mach-port, explicit increment, port release and explicit decrement stages. Final not-in-use state still exposes exact bytes through retained CF ownership. This is a recycling distinction, not final memory reclamation or GPU completion.

An initial unsealed readiness failure led to an audit-verified proceed gate before endpoint destruction. Tests caught and fixed a missing schema adapter enum. The final fault campaign repeats successfully after shared-helper changes. All 79 tests pass; controller now has 21 adapters and 19 MCP tools. Three sealed runs verify hashes/frozen sources, scoped claims are indexed, and planner/checkpoint carry the next discriminating work. Two small native goldens match the previous initial golden with zero differing bits, confirmed by system cmp.

See [findings](docs/reverse-engineering/2026-10-09-surface-failure.md), [evidence anchors](research/evidence/surface-failure-2026-10-09.json) and [goldens](tools/re/fixtures/SurfaceFailureOracle/manifest.json). R1 and R2 remain open. Next: final-release observable and frame-generation/stale-resource/delayed-completion controls; changed-method native capture diagnosis remains a parallel-in-scope serial workstream. No live Canvas wire, final kernel reclamation, GPU synchronization or portable SwiftUI claim is made.

## 2026-10-09 — delayed reuse and independent native renderer tier

Scheduled wake implemented an audit-verified owned delayed-consumer probe and reviewed `surface_reuse` adapter. Eight cases (four shapes × reused/separate storage) each repeat twice. Reused same-ID storage makes the delayed original alias observe generation-two pixels; separate surfaces preserve generation one. Two imports of the same port coalesce a local name with two send references, falling to one after first release. Five snapshot stages match independent bytes including padding and seed wrap. Remaining CF aliases retain bytes after both received rights release.

A separate owned ImageRenderer campaign pins 320×160, scale 1 and Aqua. Fresh-process A/A PNG bytes and decoded RGBA pixels are identical; changing one text label alters 1,824 pixels. Images were visually inspected. This is a native renderer oracle, not Canvas capture or hot reload. System title font remains native-environment-specific; PNGs have no embedded ICC profile.

All 83 tests pass with permitted owned subprocess-group cleanup. Default-sandbox cleanup PermissionError remains a separate diagnostic. Both campaigns seal and verify frozen sources/artifacts; scoped claims are indexed. Controller now has 22 adapters and 19 MCP tools. Sanitized surface and renderer goldens are published; prior initial surface matches the separate delayed snapshot exactly via independent system cmp.

See [findings](docs/reverse-engineering/2026-10-09-reuse-renderer.md), [evidence anchors](research/evidence/surface-reuse-renderer-2026-10-09.json), [surface goldens](tools/re/fixtures/SurfaceReuseOracle/manifest.json) and [renderer goldens](tools/re/fixtures/RendererOracle/manifest.json). R2 and O3 remain open for actual Canvas completion/capture. Next: changed-method observation and explicit portable subset using the separate renderer tier; no invented fixture field is promoted to Apple protocol semantics.

## 2026-10-09 — direct Xcode route and permission gate

Implemented a bounded direct read-only bridge diagnostic with explicit installed-Xcode selection, fresh session identity and capped local protocol logging. Sealed native run initializes but times out on window listing, without discovery or reverse server requests. Its inconclusive verdict is retained; verified artifacts and frozen sources are anchored in [sanitized evidence](research/evidence/xcode-bridge-route-2026-10-09.json).

Separately found Xcode's pending preview-reloop permission prompt through read-only UI inspection. Requested explicit approval before granting building/testing/modification access; no grant made and causal explanation remains unproven. Native user Xcode/simulator processes remain untouched.

Fixed shared-client reverse-request handling and colliding request IDs, verified by an independent owned bridge. Planner now gates capture on an actual tool response and requires changed readiness before retry. All 87 tests pass with ResourceWarning treated as an error. Toolkit: 23 adapters, 19 MCP tools. See [findings and next control](docs/reverse-engineering/2026-10-09-xcode-bridge.md). O2 and both milestones remain open.

## 2026-10-09 — retained approval and rejected Canvas content

User explicitly approved preview-reloop access and requested eliminating repeated grants. Implemented a private Unix-socket broker retaining one owned parent/mcpbridge/session. Two independent callers and subsequent separate experiment workers reuse that approval without another prompt. Canvas uses the retained connection; inactive service fails closed. No global configuration, protection change, extra package or network listener is added. Persistence after broker/Xcode exit remains unproven. Primary Apple documentation and a public proxy implementation were inspected; installed private preference names remain static candidates, not verified bypasses.

Owned RenderPreview now returns PNGs, but visual inspection falsified content acceptance: baseline repeats exactly while 2,260 changed pixels belong to the window title and actual fixture interior remains entirely white. Retained legacy supports verdict is explicitly limited to PNG/chrome checks. Corrected sealed run rejects all three captures with zero interior ink. Planner and tests prevent this failure from masquerading as rendered SwiftUI content.

All 92 tests pass. Toolkit remains 23 adapters and 19 MCP tools. See [access research and capture rejection](docs/reverse-engineering/2026-10-09-xcode-access.md), [sealed anchors](research/evidence/xcode-retained-access-2026-10-09.json) and [rejected fixtures](tools/re/fixtures/CanvasBlankOracle/manifest.json). O2/O3 and both milestones remain open; next step diagnoses blank owned view content through a changed observation while reusing live access.

## 2026-10-09 — solid rendering and enforced window cleanup

Changed owned Canvas fixtures to explicit sRGB red/blue rectangle controls. Both 32×32 center patches match exact expected RGBA, including alpha; earlier blank text/VStack content is therefore a narrower unresolved path. A separate fresh-process ImageRenderer red/red/blue control compares all 614,400 decoded RGBA bytes against independently generated literals and repeats unchanged PNG bytes exactly. Both campaigns seal and verify. No full Canvas frame or wire contract is claimed.

User required closing finished Xcode windows before opening another. Closed two stale owned workspace windows, verified no workspace windows remain, and closed welcome. Capture now refuses to open while a generated workspace remains and records its cleanup target before launch, including failures. UI agent cleanup is mandatory; unrelated projects and Xcode process remain untouched.

All 94 tests pass; toolkit remains 23 adapters and 19 MCP tools. See [findings](docs/reverse-engineering/2026-10-09-solid-controls.md), [anchors](research/evidence/canvas-solid-controls-2026-10-09.json), [Canvas patch fixtures](tools/re/fixtures/CanvasSolidOracle/manifest.json) and [independent solid fixtures](tools/re/fixtures/SolidRendererOracle/manifest.json). Next: text/layout discrimination and complete solid Canvas repeat/frame predictions, with cleanup between attempts. O2/O3 and both milestones remain open.

## 2026-10-09 — inline text discrimination

Four changed inline controls return content: plain Text, default-font stack, title-font Text and original stack without background. Visually checked plain text and no-background stack show expected labels. Dark background contributes to the last nonwhite count; counts are not OCR or glyph coverage. Blanket text/font failure is ruled out for these inputs; prior custom ProbeView blank root cause remains unproven. Next compare structurally identical inline/custom roots and establish repeat/change controls.

Sealed artifacts/frozen sources verify. Owned workspace closed at completion; no workspace windows remain. Six targeted guard tests pass against the 94-test baseline. See [findings](docs/reverse-engineering/2026-10-09-text-controls.md), [anchor](research/evidence/canvas-text-controls-2026-10-09.json) and [owned snapshots](tools/re/fixtures/CanvasTextOracle/manifest.json). O2/O3 and both milestones remain open.

## 2026-10-09 — light color scheme resolves scoped blank fixture

Matched inline/custom bodies under inherited color scheme are both blank and byte-identical; label change remains invisible. Dependent light view-environment control restores both roots, exact inline PNG/pixel repeat and a 5,910-pixel label-only change inside content. Root construction alone is ruled out; foreground/background contrast is the supported scoped explanation. Global system appearance was not changed.

Final 95-test suite passes, including chrome-only change rejection. Initial owned cleanup PermissionError retained; isolated core tests and full rerun pass. Both campaigns seal and verify. Each owned workspace closed before the next opened; final listing has no workspace windows. See [findings](docs/reverse-engineering/2026-10-09-light-root.md), [anchors](research/evidence/canvas-light-root-2026-10-09.json) and [native fixtures](tools/re/fixtures/CanvasLightOracle/manifest.json). Pinned native capture is usable; environment coverage, independent whole-frame oracle, live transport and both milestones remain open.

## 2026-10-09 — same-definition appearance reversal

One preview definition/title and body, only explicit dark/light/dark source environment changed: blank → visible → blank. Dark reversal matches all PNG bytes and decoded RGBA pixels; light interior matches the prior sealed custom light capture across 589,824 bytes. This removes the prior title confound for the owned fixture. Source mutation/restoration hashes verify; no global appearance changes.

All 98 tests pass with ResourceWarning errors enabled. Sealed native evidence verifies; owned workspace closed and final listing empty. See [findings](docs/reverse-engineering/2026-10-09-scheme-switch.md), [anchor](research/evidence/canvas-scheme-switch-2026-10-09.json) and [snapshots](tools/re/fixtures/CanvasSchemeOracle/manifest.json). Independent portable prediction, environment coverage, wire capture and milestones remain open.

## 2026-10-09 — imported Mach-name lifetime

Eight owned surface cases, each repeated twice, verify immediate lookup survives the remaining coalesced import right and fails after the final imported right drops. Retained CF aliases still preserve expected padded pixels. Eighty independent comparisons cover 51,200 bytes; two selected snapshots match earlier goldens exactly. This separates local name validity from alias lifetime, without inferring final reclamation or Canvas completion.

All 100 tests pass. Sealed native evidence verifies. Planner now avoids re-diagnosing intentional verified dark blanks, preserving the transport gate. No Xcode windows opened. See [findings](docs/reverse-engineering/2026-10-09-retired-name.md) and [anchor](research/evidence/surface-retired-name-2026-10-09.json). R1/R2 and both milestones remain open.

## 2026-10-09 — installed skills and first WASM pixel boundary

Installed reviewed, commit-pinned reverse-engineering, LLVM and Frida skills; Caveman FULL retained. Applied RE/LLVM workflows to a no-import wasm32 C literal rectangle control. Complete red/red/blue output matches 614,400 native ImageRenderer RGBA bytes; explicit row padding and ten nonmutating negative controls pass. This is a hand-authored rendering ABI, not SwiftUI compilation or broad platform execution.

All 102 tests pass after the suite caught and corrected a missing public adapter enum; initial failure retained. Toolkit now has 24 adapters and 19 research MCP tools. No Xcode windows opened. See [contract and holdouts](docs/reverse-engineering/2026-10-09-portable-solid.md), [evidence](research/evidence/portable-solid-2026-10-09.json) and [skill provenance](research/loop/skills.json). F1 and both milestones remain open.

## 2026-10-09 — native IOSurfacePayload codec keys

Recovered five native key strings through bounded ARM64 interpretation; every string matches independent Swift nominal fields. Public serializer/deserializer entrypoints and closure expose the scoped five-field codec. No generation/completion field is named inside this type; surrounding envelope/lifecycle remains unobserved.

Retained overbroad-query inconclusive run and unsupported-cmp failure; exact entrypoint query and added bounded conditional-select semantics pass. All 106 tests pass. Toolkit: 25 adapters / 19 MCP tools. No Xcode window opened; private raw disassembly remains local. See [findings](docs/reverse-engineering/2026-10-09-payload-keys.md) and [four anchors](research/evidence/surface-payload-keys-2026-10-09.json). R2/P1 and both milestones remain open.

## 2026-10-09 — codec key and identifier alias boundaries

Recovered RenderPayload, BitmapDescription and ServiceMessage key witnesses. Bitmap has nine keys versus eight fields, including byteOrder; ServiceMessage outer keys are messageType/payload despite identifier/content stored fields. Singleton identifier case returns __unique_service_message_identifier, falsifying the original metadata-name prediction in this static scope. This guides decoder/correlation work without claiming live reply matching.

Two unsupported-entry failures and the original prediction counterexample are sealed and retained; bounded thunk/register/constant entry support and signed branch checks yield supporting dependent controls. All seven runs verify; all 109 tests pass. No Xcode windows opened. See [findings](docs/reverse-engineering/2026-10-09-codec-boundaries.md) and [seven anchors](research/evidence/codec-key-boundaries-2026-10-09.json). R2/P1/P2 and both milestones remain open.
