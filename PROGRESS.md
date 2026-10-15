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

## 2026-10-09 — optional service identifier encode/decode sites

Followed the outer ServiceMessage serializer into its payload getter. Static archive and unarchive call sites select the singleton identifier key and Swift.String conformance, with an optional value API; initializer stores the returned value before content dispatch. This narrows where correlation data travels, without establishing reply propagation or malformed-value behavior.

Four new sealed runs verify; missing-signature closure selector failure is retained and corrected. Campaign validates; existing 109-test implementation checkpoint unchanged. No Xcode windows opened. See [static path](docs/reverse-engineering/2026-10-09-service-identifier.md) and [four anchors](research/evidence/service-identifier-path-2026-10-09.json). R2/P1/P2 and both milestones remain open.

## 2026-10-09 — final-reference global ID reachability

Immediate global IOSurface-ID disappearance fails in two of 16 owned executions despite peer exit and reviewed right/alias cleanup. Retained failure prevents premature reclamation claims. Separately registered requested-100ms control passes all 16 executions with 80 independent padded-byte comparisons (51,200 bytes); its immediate lookups were already null, so delay causality remains unproven.

Both campaigns seal and verify; all 110 tests pass. No Xcode windows opened. See [scope and failed prediction](docs/reverse-engineering/2026-10-09-surface-id-lifetime.md) and [anchors](research/evidence/surface-id-lifetime-2026-10-09.json). R1/R2 and both milestones remain open.

## 2026-10-09 — transport reply success/error boundary

Static TransportReply result closure invokes captured callback with encoded LazyPropertyList plus null error on success, or null payload plus serializable NSError on failure. Dependent encoder has OS14.4 data/dictionary branches and selected serialization-error fallbacks. A null callback error alone does not prove payload serialization succeeded; no live reply matching or exactly-once completion is established.

Two sealed runs verify against unchanged image identity and prior identifier anchors. Added campaign validates; existing 110-test implementation checkpoint unchanged. No Xcode windows opened. See [static path and limits](docs/reverse-engineering/2026-10-09-transport-reply.md) and [anchors](research/evidence/transport-reply-path-2026-10-09.json). P1/P2/R2 and both milestones remain open.

## 2026-10-09 — owned data decode and empty fallback

Implemented finite native UVPropertyList data decoding controls. All eight inputs retain exact data bytes across independent helpers; two valid dictionaries decode exactly, while six invalid/non-dictionary inputs expose empty dictionaries. Foundation legacy ASCII string parsing is measured separately from Python binary-plist decoding. Empty dictionary alone cannot establish valid serialization.

Initial BOOL-boxing/parser-domain harness failure retained; tests catch absent-None canonicalization. Corrected native run supports; all 113 tests pass. Both seals and prior reply anchors verify. No Xcode windows opened. See [measured boundary](docs/reverse-engineering/2026-10-09-plist-data-decode.md) and [anchors](research/evidence/plist-data-decode-2026-10-09.json). Full live reply/optional-field acceptance remains open.

## 2026-10-09 — static continuation completion guard

Followed public resume forwarding into initializer-owned lock/fulfill/unlock guard. Exact unit-state specialization sets first-fulfillment flag and outcome 0; already-fulfilled handler returns outcome 1 on its normal path. The closure skips user callback for tag 1 and invokes it outside the lock. This is static completion intent, not native race/reentrant/cancellation proof.

Implemented fail-closed guard-pattern validation with negative evidence controls; all 115 tests pass. Five native runs and prior reply anchors verify. No Xcode windows opened. See [guard and runtime limits](docs/reverse-engineering/2026-10-09-continuation-guard.md) and [anchors](research/evidence/continuation-guard-2026-10-09.json). R2 and milestones remain open; a safe typed native runtime constructor is not yet established.

## 2026-10-09 — independent WASM interpreter and rejection controls

Extended the owned rectangle adapter to installed WasmKit 0.1.6. A separately compiled zero-import checker uses sealed native RGBA arrays and independent padding; V8 and WasmKit execute exactly the same module. Four cases compare 614,432 bytes, eight injected pixel/final-byte faults each report one mismatch, and ten invalid requests preserve the entire buffer (2,048,000 bytes per engine). Three checker holdouts reject explicitly.

Unsealed untyped CLI crash retained separately; typed arguments correct the harness. Three substantive sealed campaigns verify, and 117 tests pass. No Xcode windows opened. See [runtime scope](docs/reverse-engineering/2026-10-09-portable-second-runtime.md) and [anchors/controls](research/evidence/portable-second-runtime-2026-10-09.json). Both runtimes ran on macOS; SwiftUI source compilation, browser/non-Apple execution and both milestone acceptance gates remain open.

## 2026-10-09 — duplicate completion policy and alias/body acceptance

Recovered exact continuation duplicate target → shared diagnostic handler → private failure-policy dispatch. Static paths distinguish callback, logging, assertion helper and fatal call/trap. Default getter writes tag 2; named case/payload mapping and native behavior remain unverified. Duplicate completion cannot be described as uniformly returning without diagnostics.

Fixed disassembly acceptance: headings no longer certify bodies; bounded address fallback preserves instruction bits; same-address aliases retain one body without overwrites. Six seals verify, including heading-only result quarantined for body claims, failed alias accounting and private-name query miss. Initial owned-process cleanup permission failure retained; authorized rerun passes all 119 tests. No Xcode windows opened. See [scope/failures](docs/reverse-engineering/2026-10-09-continuation-policy.md) and [anchors](research/evidence/continuation-policy-2026-10-09.json). R2 and both milestones remain open.

## 2026-10-09 — default diagnostic representation and cancellation action guard

Resolved complete default constant pair `(1,0)` plus tag 2 to reviewed assertion-helper path. Exact helper has analytics call and normal return without direct fatal trap; no policy was executed and no named enum case inferred. Cancellation entry selects same fulfillment state/duplicate target, returns for outcome 1, and dispatches indirect action after unlock on first fulfillment.

Added strict default/cancellation structural control modes with mutated dataflow, bounds, condition and action-boundary tests. Four seals verify; prior eleven continuation/policy anchors verify; 124 tests pass. No Xcode windows opened or private Swift calls used. See [scope](docs/reverse-engineering/2026-10-09-cancellation-default.md) and [anchors](research/evidence/cancellation-default-2026-10-09.json). Native races, action identity, release and live transport remain open.

## 2026-10-09 — live-peer late acknowledgement and endpoint revocation

Paired owned controls observe completion receive timeout before releasing live peer through handshake. Open reply endpoint accepts/audit-verifies late acknowledgement; explicit endpoint revocation yields INVALID_DEST. Both peers gracefully release surface rights/CF aliases/inbox/reply names, with exact imported, post-timeout and sender retained bytes.

Sixteen executions yield 48 padded-byte comparisons (30,720 bytes); all eight cases repeat. Shared-helper misplaced check caught during review and corrected; original three-phase fault corpus passes. Three seals verify; 127 tests pass. See [scope/review](docs/reverse-engineering/2026-10-09-surface-late-ack.md) and [anchors/comparisons](research/evidence/surface-late-ack-2026-10-09.json). Owned timeout policy is not native Canvas behavior; reclamation/GPU/races remain open. No Xcode windows opened.

## 2026-10-09 — unfulfilled-state destruction diagnostic

Recovered state snapshot/case-1 diagnostic skip and other-case Unfulfilled error/failure policy before normal reference cleanup. Deallocating destructor forwards to that body and class deallocation; no physical resource reclamation claim. Independent nominal metadata declares waiting/fulfilled, without assigning runtime tags; seven broader parser errors and unresolved payload types retained.

Added finite destructor/target-metadata control modes and mutation controls. Initial wrong acceptance-field run retained inconclusive; corrected target checks pass. Four seals verify; 129 tests pass. See [scope](docs/reverse-engineering/2026-10-09-unfulfilled-deinit.md) and [anchors](research/evidence/unfulfilled-deinit-2026-10-09.json). Native abandoned callback/reply behavior, race/resource accounting and transport remain open. No Xcode windows opened.

## 2026-10-09 — cancellation callback and actor boundaries

Recovered both concrete callback invoke bodies and specialized constructors. Isolated invoke optionally calls actor verification before dispatching its stored closure; concurrent invoke dispatches directly. A dependent probe shows the verification helper calls Swift `preconditionIsolated`; no executor-hop or concrete transport action is established. Added two finite structural controls and corruption checks for context, branch, callee, initialization, helper extent and duplicate evidence. Five runs sealed and anchor-verified; 131 tests pass. R2 remains open; no Xcode windows opened.

Evidence: [callback boundaries](docs/reverse-engineering/2026-10-09-cancellation-callbacks.md), [sanitized seals](research/evidence/cancellation-callbacks-2026-10-09.json). Native runtime witness association, selected caller closure, races, abandoned replies and resource cleanup remain required.

## 2026-10-09 — invalidation cancellation gates

Recovered shared invalidation-token closure weak-owner skip and lock/update/unlock/owner-release/result-cleanup ordering. A dependent merged update probe shows state byte `0x41 == 1` bypasses mutation, with a separate result tag. Added a finite checker including encoded ARM64 handoff targets and corrupted weak/state/lock/outcome controls. Four runs sealed and anchor-verified; 132 tests pass. Called dictionary effects, native races, selected-flow association and transport cancellation remain unverified; R2 stays open. No Xcode windows opened.

Evidence: [invalidation gates](docs/reverse-engineering/2026-10-09-invalidation-cancellation.md), [sanitized seals](research/evidence/invalidation-cancellation-2026-10-09.json).

## 2026-10-09 — owned GPU completion and retained surface access

Added public Metal/IOSurface shared-BGRA render-clear control. Four geometries, two helper repeats, and red/red/blue results match independent literal pixels plus every row-padding/allocation-tail byte. Completion handler/status/error evidence gates CPU read. A dependent probe drains command scopes and drops explicit Metal texture/queue references; retained CF blue snapshots remain exact. Corrected initial control checks 524,288 bytes; retained-access control checks 655,360 bytes. Initial Boolean boxing harness rejection retained, fixed with explicit numberWithBool. Three seals anchor-verified; 135 tests pass. R1/R3 remain open for GPU transfer, Canvas synchronization, timeouts and final reclamation. No Xcode windows opened.

Evidence: [GPU control](docs/reverse-engineering/2026-10-09-gpu-surface-completion.md), [sanitized seals](research/evidence/gpu-surface-completion-2026-10-09.json).

## 2026-10-09 — GPU-produced surface Mach handoff

Connected bounded public Metal render completion to the owned audited receiver-first Mach control. CPU peer imports GPU red/blue storage, mutates and exits cleanly or abruptly; producer retains full allocation/port-only access and checks local send-right counts. Independent producer/peer/padding/tail comparisons pass: 16 executions and 1,572,864 bytes per GPU campaign, repeated in two seals. Added identity/status/type/extent/exit/rights/byte fault controls; 138 tests pass. Original CPU sender-first and receiver-first campaigns rerun successfully. Four new seals anchor-verified; R1/R3 remain open for cross-process GPU execution, Canvas synchronization, failures and final reclamation. No Xcode windows opened.

Evidence: [GPU Mach boundary](docs/reverse-engineering/2026-10-09-gpu-mach-handoff.md), [sanitized seals](research/evidence/gpu-mach-handoff-2026-10-09.json).

## 2026-10-09 — receiving-process GPU readback

Extended owned GPU Mach handoff with receiver Metal texture-to-buffer blit on imported IOSurface before CPU mutation/exit. Independent shared destination initialization, active pixels, row padding and allocation-tail predictions pass: 16 executions, 128 whole allocation comparisons and 2,097,152 bytes per consumer campaign. Two consumer seals and producer-only regression pass. Strict identity/status/type/layout/missing-readback/padding faults reject; 140 tests pass. Three new seals anchor-verified. Ordered public Metal control only; Canvas, unsynchronized overlap, failures and final reclamation remain open. No Xcode windows opened.

Evidence: [peer GPU readback](docs/reverse-engineering/2026-10-09-gpu-peer-readback.md), [sanitized seals](research/evidence/gpu-peer-readback-2026-10-09.json).

## 2026-10-09 — owned GPU event timeout and recovery

Added a receiving-process shared-event gate before GPU blit. Initial 20ms completion wait times out without callback; explicit event signal then permits exactly one successful late completion, followed by exact whole-allocation comparisons and existing clean/abrupt exit/local-right cleanup. Two timeout campaigns and ordinary GPU readback regression pass, each comparing 2,097,152 bytes. All 32 timeout executions observed committed status2, so GPU arrival and scheduling delay remain unproven. Three seals anchor-verified; 142 tests pass. Canvas timeout/cancellation policy and final reclamation remain open. No Xcode windows opened.

Evidence: [event timeout control](docs/reverse-engineering/2026-10-09-gpu-event-timeout.md), [sanitized seals](research/evidence/gpu-event-timeout-2026-10-09.json).

## 2026-10-09 — owned GPU frame reuse after timeout

Receiving process now reuses the same imported surface, texture, destination buffer, queue and increasing event values through original/opposite/restored frames. Every command observes bounded pending timeout then explicit signal/late completion before snapshots; full source/destination active pixels, row padding and allocation tails match independent expectations. Existing clean/abrupt exit and local-right cleanup still pass after restoring original content. Three reuse campaigns each compare 3,145,728 bytes; prior event-timeout regression passes. Four seals anchor-verified; 145 tests pass, including stale-frame/resource/sequence/padding rejection. Resource identity is not frame content in this owned GPU fixture. R1/R2/R3 remain open for actual Canvas policy, concurrent reuse and final reclamation. No Xcode windows opened.

Evidence: [GPU reuse control](docs/reverse-engineering/2026-10-09-gpu-frame-reuse.md), [sanitized seals](research/evidence/gpu-frame-reuse-2026-10-09.json).

## 2026-10-09 — native observer dictionary removal

Followed instruction-derived invalidation targets into isolated setter/remover, concurrent remover, native bucket deletion and identifier-array removal. Mapped16-byte sentinel `(0,1)` selects static removal branch; found/uniqueness/ordered-key gates, missing-key traps, bucket occupancy/count/counter writes, array shift/count decrement and12 encoded call targets now have finite corruption-tested checks. Five discovery/dependency/control seals anchor-verified;150 tests pass. Value-witness/runtime contents, native callback association, races and transport/resource cleanup remain unverified; R2 stays open. No Xcode windows opened.

Evidence: [dictionary removal boundaries](docs/reverse-engineering/2026-10-09-observer-dictionary-removal.md), [sanitized seals](research/evidence/observer-dictionary-removal-2026-10-09.json).

## 2026-10-09 — pinned REA integration

- Installed REA 6.2.0 locally with a committed npm lock, disabled lifecycle scripts and a repository-local cache. Added reproducible bootstrap; no paid provider required.
- Registered the matching Codex MCP and skill, preserved unrelated configuration and retained its backup. Measured 139 tools; selected 35 native/Apple/evidence tools with bounded deadlines and explicit free Ghidra binding.
- Added serial `rea_native` adapter, strict target/parameter checks, frozen manifests and runtime-code identity. Owned ARM64 function decompilation passes independent mapping, all four selected instruction bytes and encoded BL destination/reference/flow checks; owned provider closes cleanly.
- Retained the FoundationHost 330-second import timeout, architecture-alias rejection and successful-but-inconclusive campaign-path run. Corrected the observed schema alias and acceptance paths; 159 tests pass.
- Published sanitized [evidence](research/evidence/rea-integration-2026-10-09.json) and [integration/runbook guidance](docs/reverse-engineering/rea-integration.md). Full-image REA import requires a changed analysis method before retry; actual Canvas transport/runtime and both milestone contracts remain incomplete.

## 2026-10-09 — token callback association and live REA audit

- Connected isolated/concurrent token capture forwarders to distinct removal/update adapters, then shared weak-owner guarded lock/update/unlock and numeric state guard. Result consumption remains a separate unknown body.
- Compared every one of 632 captured instruction bytes across ten selected entries with mapped native bytes; independently decoded six pointers, thirteen direct targets and the null/state branches. Two accepted repeats; all six runs, including count-prediction and annotation failures, retained.
- Added mutation-tested checker and strict controller flag; 166 tests pass. Published [evidence](research/evidence/token-callback-link-2026-10-09.json) and [scope/unknowns](docs/reverse-engineering/2026-10-09-token-callback-link.md).
- Confirmed REA connected in the live desktop session with all 35 configured tools. Direct Xcode Mach-O inspection succeeds and its complete UUID matches independent parsing. Metadata uses `native-macos`; full Ghidra import remains blocked separately. No setup/restart repetition or Xcode windows needed.

## 2026-10-09 — anonymous token result consumer

- Added bounded explicit native instruction ranges for unnamed helpers, with alignment/extent/section/duplicate validation.
- Recovered the five-instruction consumer's low-byte-equals-one gate and unchanged payload register before release tail dispatch. Compared all 20 consumer and 12 stub instruction bytes against independently mapped native bytes.
- Independently verified stub/pointer indirect indices, undefined external symbol and dylib ordinal: declared `_swift_bridgeObjectRelease` import from Swift core. Runtime interposition and actual deallocation remain unknown.
- 65,542 finite static flag cases agree with an independent numeric oracle; four accepted seals retained; 176 tests pass. Published [evidence](research/evidence/token-result-consumer-2026-10-09.json) and [scope](docs/reverse-engineering/2026-10-09-token-result-consumer.md). Actual runtime/transport/resource reclamation acceptance stays open.

## 2026-10-09 — Token metadata and witness dispatch

Recovered complete copy/destroy dispatch and metadata resolver bodies:216 independently mapped instruction bytes plus12 import-stub bytes.65,540 cache gate cases agree with zero/parity expectations. Four sealed runs retained; first two prove acquisition only.181 automated tests pass, including every-byte and matching-image instruction mutations. Concrete metadata/witness ownership effects, runtime releases, races and Canvas transport remain open; no Xcode windows launched. See [evidence](research/evidence/token-value-witness-2026-10-09.json) and [analysis](docs/reverse-engineering/2026-10-09-token-value-witness.md).

## 2026-10-09 — Token symbolic type records

Resolved two specialized State type records through embedded-NUL symbolic parsing and validated dyld chained rebases.72 wrapper instruction bytes compared; ten nominal references,62 bounded record/terminator bytes and16 zero disk-cache bytes checked. Three accepted anchored seals;190 tests pass. Initial literal-name expectation was falsified and corrected to nested State with verified FulfillOnceState parent. Runtime metadata, concrete witness targets/effects and ownership remain unproven. No Xcode windows opened. [Evidence](research/evidence/token-symbolic-descriptors-2026-10-09.json), [analysis](docs/reverse-engineering/2026-10-09-token-symbolic-descriptors.md).

## 2026-10-09 — Generic State witness pattern

Verified State generic descriptor/pattern and eight chained witness targets;648 body and48 import-stub instruction bytes compared,16 pattern bytes independently predicted.132,098 direct-tag layout projections and complete57-byte overlapping trailer copy pass. Three seals retained: first acquisition range included neighboring helper, final controls narrow instantiator to8 bytes.197 tests pass. No runtime specialization, retain/release accounting or transport claim. [Evidence](research/evidence/state-witness-pattern-2026-10-09.json), [analysis](docs/reverse-engineering/2026-10-09-state-witness-pattern.md).

## 2026-10-09 — Storage/trace bridge delegation

Verified declared payload witness copy/destroy delegation:192 body+24 import instruction bytes; storage copies24 bytes and delegates three reference words, trace copies8 bytes and delegates one. Pattern/static metadata associations and reflection names checked.130 owned null/alias models compare3,040 bytes without invoking Swift. Six seals retained (three acquisition, three full controls);204 tests pass. Shared stub verifier now rejects duplicate instruction rows. Actual runtime selection, reference counts, reclamation and Canvas transport remain open. [Evidence](research/evidence/storage-bridge-delegation-2026-10-09.json), [analysis](docs/reverse-engineering/2026-10-09-storage-bridge-delegation.md).

## 2026-10-09 — State named case indices

Recovered State waiting0/fulfilled1 from defined case-index symbols, eight predicted constant bytes and enum reflection, with three witness rebases and424 mapped instruction bytes.132,098 finite direct-tag models compare28,088,564 whole-buffer bytes including padding; no native State invocation. Three seals retained (one acquisition, two controls);211 tests pass. Result discriminator, runtime/races and Canvas cleanup remain distinct/open. [Evidence](research/evidence/state-case-tags-2026-10-09.json), [analysis](docs/reverse-engineering/2026-10-09-state-case-tags.md).

## 2026-10-09 — Separate update-result witness boundary

Verified separate WaitingStateUpdateResult reflection, generic pattern and four witness rebases. Complete 684 body and 24 import instruction bytes compare independently; 132,098 numeric direct-tag models preserve 23,227,146 whole-buffer bytes including padding. Result uses max(sizeA,sizeB), unlike State trailer layout. Three seals retained including overbroad initial acquisition and falsified instantiator prediction; corrected control and 215 tests pass. Numeric case names and live result/ownership/race/transport remain open. [Evidence](research/evidence/update-result-witness-2026-10-09.json), [analysis](docs/reverse-engineering/2026-10-09-update-result-witness.md). No Xcode windows opened.

## 2026-10-09 — Literal source-to-IR feasibility

Implemented explicit opaque sRGB Color.frame expression subset through generated C and saved LLVM IR to import-free WASM. Full native RGBA comparison covers 614,400 bytes; independent literals/padding cover 614,432 bytes. Repeat normalized IR/module bytes match; 15 unsupported-source holdouts and 16 full-buffer invalid-stride controls pass. Four seals retain two inconclusive filename-metadata comparisons and subsequent precise sRGB contract. 221 tests pass. No general SwiftUI/non-Apple/browser/Canvas or hot-reload claim; F1/F2 stay open. [Evidence](research/evidence/literal-source-ir-2026-10-09.json), [contract and limits](docs/reverse-engineering/2026-10-09-literal-source-ir.md). No Xcode windows opened.

## 2026-10-09 — Source renderer independent interpreter

Linked unchanged saved source renderer IR with a separate non-LTO whole-allocation checker. WasmKit/V8 agree on all 40 controls; 12 pixel/padding/unused-tail faults are detected and 16 invalid strides preserve complete buffers. Baseline 819,200 and invalid-request 3,276,800 allocation bytes compare per interpreter. Two accepted seals; 223 tests pass. Diagnostic modules are separate from standalone modules; both hosts remain macOS, and F2/non-Apple/Canvas gates stay open. [Evidence](research/evidence/source-second-interpreter-2026-10-09.json), [scope](docs/reverse-engineering/2026-10-09-source-second-interpreter.md). No Xcode windows opened.

## 2026-10-10 UTC — Anchored source WASM on Linux ARM64

Exact sealed standalone/diagnostic modules execute in Wasmtime49 on existing Colima Linux VM. Direct allocations compare819,200 bytes;16 invalid requests preserve3,276,800 allocation bytes;614,432 pixel bytes match macOS V8;40 diagnostic controls agree with WasmKit/V8. Zero imports, owned-container cleanup, existing user container still running. Two accepted seals;227 tests after retained campaign-schema failure/fix.27 adapters/19 MCP tools. Narrow Linux execution gate passes; source compiler still macOS and broader SwiftUI/Canvas/browser/performance remain open. [Evidence](research/evidence/linux-source-wasm-2026-10-10.json), [scope](docs/reverse-engineering/2026-10-10-linux-source-wasm.md). No Xcode windows opened.

## 2026-10-10 UTC — Retired Mach name aliasing under churn

Two sealed owned native campaigns observe28 exact retired-name recurrences across2,048 replacement-right lifecycles. Old name resolves replacement ID only on exact recurrence; send refs and name removal pass.786,432 complete allocation bytes compare including padding/tail.232 tests pass; four inconclusive seals retain sandbox denial, unsupported explicit rename and strict serialization failure. Raw numeric names require lifetime/generation protection; no Canvas protocol or physical reclamation claim. R1/R2 stay open. [Evidence](research/evidence/surface-name-churn-2026-10-10.json), [scope](docs/reverse-engineering/2026-10-10-surface-name-churn.md). No Xcode windows opened.

## 2026-10-10 UTC — Retained-right delayed-read protection

Two owned retained-mode seals keep original surface ID through2,048 replacement-right lifecycles after producer CF owner drops. Delayed original allocation remains exact; original final right/name cleanup passes. Same-helper released contrast aliases10 times in1,024 lifecycles.1,441,792 whole allocation bytes compare including padding/tail.234 tests pass after retained queue-selection test failure/fix. Resource identity protection established for bounded one-task CPU control; mutable-frame generations, Canvas and physical reclamation remain open. [Evidence](research/evidence/retained-name-churn-2026-10-10.json), [scope](docs/reverse-engineering/2026-10-10-retained-name-churn.md). No Xcode windows opened.

## 2026-10-10 — Delivery graph and extended Canvas loop

Added30-node/47-edge acceptance/research graph, anchored quarantine, blocked prerequisites, downstream ranking and completed-research skipping. Existing heartbeat extended through declared native RE then cross-platform WASM Canvas acceptance. Graph-selected native-backed reconstruction commit policy passes128 controls twice;102,400 padded image bytes compare. First compile failure exposed stale shared-helper CPU signatures; repaired reuse/failure callers, retained failure, R1 failure/timeout12 cases pass.243 tests. Both milestone gates remain open; next independent ready task is browser execution. [Graph and scope](docs/reverse-engineering/2026-10-10-graph-loop.md), [evidence](research/evidence/graph-generation-2026-10-10.json). No Xcode windows opened.

## 2026-10-10 — Actual browser source WASM and Canvas2D

Two sealed browser campaigns/two fresh loads each execute exact anchored owned source modules;3,276,800 baseline bytes,13,107,200 per-invalid-request allocation bytes and2,457,696 Canvas2D opaque RGBA bytes compare exactly. Frozen-template failure retained/fixed;247 tests pass. Loopback servers and owned browser tabs close; no Xcode windows opened. Browser research gate complete, F2 and milestones remain open. Graph selects native alpha/compositing oracle next. [Evidence](research/evidence/browser-source-wasm-2026-10-10.json), [scope](docs/reverse-engineering/2026-10-10-browser-source-wasm.md).

### 2026-10-10: alpha quantization falsification

[Native alpha oracle](docs/reverse-engineering/2026-10-10-native-alpha.md) retains symmetric half-rounding contradiction and artifact-cap failure. Revised quantized-alpha complementary model passes two fresh holdouts and all8 cases in two campaigns:19,584 decoded RGBA bytes;249 tests. Owned goldens published. Next portable alpha control remains separate from opaque source parser; native Canvas/transport and milestone acceptance stay open.

### 2026-10-10: owned compiler cleanup

[Owned descendant tracking](docs/reverse-engineering/2026-10-10-owned-process-quiescence.md) now preserves ancestry across root exec and reparenting/group changes. Two corrected campaigns stop four detached late writers and two actual Swift compiler artifact-limit runs; finite cache snapshots and seals remain stable. Initial tracking failure retained, explicit quarantine visible in graph;253 tests pass. Next portable alpha control. Arbitrary between-poll escape/exec and indefinite quiescence remain outside measured claims; both milestone acceptance gates stay open.

### 2026-10-10: portable alpha reconstruction

[Native-backed alpha WASM](docs/reverse-engineering/2026-10-10-portable-alpha.md) matches8 native cases plus independent padded/tail allocations in two campaigns:216 frames,3,538,944 baseline bytes,393,216 invalid bytes,19,584 native bytes. V8/WasmKit native-array checker detects48 mutations; renderer/checker modules repeat exactly.256 tests. Opaque source parser unchanged. Next actual browser alpha readback; F2 and both milestones remain open.

### 2026-10-10: actual browser alpha boundary

[Browser alpha control](docs/reverse-engineering/2026-10-10-browser-alpha.md) compares72 frames across four actual page loads:1,179,648 complete baseline bytes,4,718,592 invalid bytes,44,064 Canvas2D bytes,19,584 native bytes.259 tests; owned tabs/servers closed. Primary-red alpha and red-over-blue only; opaque source parser unchanged. Next actual Linux alpha execution; both milestones remain open.

### 2026-10-10: actual Linux alpha boundary

[Linux alpha control](docs/reverse-engineering/2026-10-10-linux-alpha.md) matches324 fresh full allocations in three campaigns:5,308,416 independent bytes and the same extents cross-host,589,824 invalid bytes,29,376 native bytes.96 checker cases/72 mutations;262 tests. Offline owned containers removed, existing containers preserved. macOS compilation and Apple-hosted Linux VM disclosed. Next native mixed-color alpha oracle; F2 and both milestones remain open.

### 2026-10-10: native mixed-color alpha counterexamples

[Mixed-alpha boundary](docs/reverse-engineering/2026-10-10-native-mixed-alpha.md) repeats68 captures/41,616 RGBA bytes. Two independent campaigns discriminate three predeclared formulas; a revised ties-to-even model matches original cases but fails every new half-tie holdout pair. All failures and seals retained;266 tests. Portable subset unchanged. Next raw CGImage/Color precision versus export boundary; native Canvas and both milestones remain open.

### 2026-10-10: raw mixed-alpha export boundary

[CGImage/export control](docs/reverse-engineering/2026-10-10-native-mixed-boundary.md) measures84 native captures/51,408 raw bytes in three supported campaigns. Mixed rounding counterexamples already exist before TIFF/PNG export; both exports match measured-raw unpremultiplication exactly. Latest28 legacy outputs equal sealed prior native measurements.271 tests; failed layout probe retained. Native stride68 has no padding. Next independent CGContext contrast; Canvas and both milestones remain open.

### 2026-10-10: independent Quartz and public-color contrast

[Quartz producer controls](docs/reverse-engineering/2026-10-10-native-mixed-quartz.md) compare280 native allocations/201,600 bytes/30,240 sentinel padding bytes, with140 repeats. Direct Double half-up predictions pass; public color routes still differ from ImageRenderer in five cases. Copy versus normal allocation bytes agree exactly in a separately sealed112-pair contrast. Harness failures retained;278 tests. Next public ImageRenderer drawing callback into owned padded context; Canvas and both milestones remain open.

### 2026-10-10: public renderer callback and layout matrix

[Drawing callback controls](docs/reverse-engineering/2026-10-10-native-mixed-callback.md) compare280 target allocations/189,504 bytes/18,144 padding bytes and140 repeat pairs. One native half-tie case still differs:blue7 versus cgImage8. Both blend states and all four stride/bitmap targets have equal active pixels; full padded comparisons remain separate.283 tests; all seals verified. Next same-instance getter/callback order probe; Canvas and both milestones remain open.

## 2026-10-10 — same-instance renderer order

Same-instance public renderer order:56 fresh processes,224 immediate provider copies plus224 retained snapshots (274,176 bytes),112 callbacks (80,640 complete bytes including12,096 padding). All168 repeat pairs and168 call-order pairs equal. Getters and retained provider bytes stable across both callbacks and nsImage export; case12 remains blue8 getter versus7 callback in all8 targets. Reused56 exports/34,272 decoded bytes satisfy224 measured-provider relations,28 repeat pairs and28 order pairs. No general color formula or native Canvas wire claim.

287 tests pass. Evidence: [same-instance renderer order](docs/reverse-engineering/2026-10-10-native-mixed-order.md). Both milestones remain open.

## 2026-10-10 — rasterization scale and grouping

Public renderer scale and drawingGroup controls:112 fresh processes,448 exact-count callbacks/allocations,322,560 full bytes including48,384 unchanged padding bytes. Scales1/2/0.5/4 in both orders preserve prior callback pixels:448/448; getter relation416/448,onlycase12 differs. All224 repeat and224 order pairs pass. Explicit drawingGroup modifier produces equal bytes but does not prove an offscreen pass was executed. General mixed-color formula and native Canvas protocol remain open.

290 tests pass. Evidence: [scale and grouping](docs/reverse-engineering/2026-10-10-native-mixed-scale.md). Both milestones remain open.

## 2026-10-10 — independent primary-layer composition

Primary-layer composition:128 fresh processes,512 callback/getter targets;368,640 full callback bytes including55,296 unchanged padding bytes and313,344 getter bytes.512 repeat pairs,384 scale/group matrix pairs and layer-order positive controls pass. Independently predeclared quantized-stage source-over predicts512/512 callbacks, including128/128 new holdouts, but only400/512 getters. Getter boundary remains distinct; no universal color or native Canvas protocol claim.

293 tests pass. Evidence: [primary-layer composition](docs/reverse-engineering/2026-10-10-native-primary-layers.md). Both milestones remain open.

## 2026-10-10 — portable primary-layer callback contract

Portable primary-layer callback-target control:320 fresh V8 instances/5,242,880 complete allocation bytes;80 native-prefix comparisons/57,600 native target bytes plus independently checked tails;160 repeat pairs;17 invalid requests/278,528 unchanged bytes. Import-free C-to-LLVM-to-WASM. Native checker40 targets×5 modes in V8 and WasmKit,160 channel/alpha/padding/tail faults per runtime. Two semantic algorithm mutants detected by full native checks; endpoint controls preserved, paired runtime witness counts agree. Getter/PNG differs; no Canvas or SwiftUI compatibility claim.

297 tests pass. Evidence: [portable primary layers](docs/reverse-engineering/2026-10-10-portable-primary-layers.md). Both milestones remain open.

## 2026-10-10 — actual Linux primary-layer execution

Actual Linux ARM64 Wasmtime49 primary-layer execution:320 complete allocations/5,242,880 independent bytes plus same extent cross-host equality;80 full native-prefix comparisons/57,600 reused native target bytes;17 invalid requests/278,528 unchanged bytes.200 native checker controls including160 channel/alpha/padding/tail faults. Both semantic mutants rejected;all80 per-case counts match anchored V8. Owned containers removed,two existing containers preserved. Getter/PNG differences remain;no Canvas/SwiftUI equivalence.

301 tests pass. Evidence: [Linux primary layers](docs/reverse-engineering/2026-10-10-linux-primary-layers.md). Both milestones remain open.

## 2026-10-10 — strict primary-layer source subset

Strict primary-layer ZStack.frame source-to-C-to-saved LLVM IR-to-WASM:16 modules,64 full V8 frames/1,048,576 bytes,28 native-prefix comparisons/20,160 target bytes,64 no-write invalid requests,160 baseline/fault cases per interpreter. Repeat/whitespace IR and module bytes equal. Swift parse-only oracle exposed3 missing-separator acceptances; retained inconclusive seal, enforced newline/semicolon separators, fixed oracle agreement and22 diagnostic holdouts. Final complete pipeline supports;getter/PNG/Canvas distinctions retained.

304 tests pass. Evidence: [primary-layer source subset](docs/reverse-engineering/2026-10-10-primary-source-subset.md). Both milestones remain open.

## 2026-10-10 — actual Linux primary-layer source modules

Actual Linux ARM64 Wasmtime49 executes16 pinned source-derived modules:64 complete allocations/1,048,576 bytes agree with independent Fraction expectations and macOS V8;28 native-prefix frames reuse20,160 measured native bytes.64 invalid renderer requests preserve full allocations.160 checker controls include128 exact-one faults,16 aggregates pass.64 invalid checker calls return sentinel and preserve all128KiB linear memory/8,388,608 bytes against their observed valid-call baseline. Missing-export harness failure retained; corrected using actual exported memory. Source/config/IR/module hashes checked, owned containers removed and two existing containers preserved. Frontend remains macOS;native getter/PNG differs;no native Canvas/general SwiftUI claim.

307 tests pass. Evidence: [Linux primary-layer source](docs/reverse-engineering/2026-10-10-linux-primary-source.md). Both milestones remain open.

## 2026-10-10 — browser source adapter and exact verifier efficiency

Implemented actual-browser primary-source page/adapter with full native/model allocation, invalid-stride, checker fault/sentinel and explicit premultiplied-to-straight sRGB Canvas2D verifiers. Synthetic corruption controls pass. Actual execution blocked by locked Mac;automatic approval review rejected launch and prohibited indirect workarounds. No browser run, runtime seal or graph completion claimed. Browser awaits unlocked/approved prerequisite;independent source CLI/cache work remains eligible.

Full suite first interrupted at five-minute budget in repeated equal-byte expansion. Complete64KiB native byte equality now skips diagnostic expansion only for equal chunks, after hashing/counting every byte. Independent exhaustive boundary/bit/tail/hash controls preserve exact diagnostics;no sampling/normalization.311 tests pass in61.670 seconds;page JavaScript syntax passes. Evidence:[browser adapter and blocker](docs/reverse-engineering/2026-10-10-browser-primary-source.md). Both milestones remain open.

## 2026-10-10 — primary-layer source CLI and build cache

Implemented explicit source-to-WASM CLI, content-addressed semantic cache with exact source provenance and atomic single published-bundle pointer.4 CLI builds include2 cache hits;changed order creates a new key. Every saved IR/module byte equals independently pinned output.16 fresh V8 frames/262,144 full independent bytes plus5760 reused native callback-target bytes;16 invalid requests preserve262,144 bytes.7 unsupported/cache/compiler/linker/pre-publication controls preserve prior pointer/module;staging cleaned. Named-linker alias failure retained and independently falsified/fixed. Complete producer/normalizer/compile/link/tool identities bind cache reuse;local consistency is not authenticity.

315 tests pass. Evidence:[source CLI/cache](docs/reverse-engineering/2026-10-10-primary-source-cli.md). macOS compilation/V8 only;no active runtime/state hot reload, general SwiftUI or native Canvas claim. Both milestones remain open;browser prerequisite unchanged.

## 2026-10-10 — Native primary-layer extent holdouts

80 public native callback captures match every independent allocation byte at compact/padded 1×1,13×7,64×64 targets: 1,310,720 bytes, including 1536 padding and1,035,264 unused-tail bytes. 40 repeat pairs match. Two insufficient-artifact-budget failures retained with valid seals; corrected 256 MB/180 s final run supports. 337 working-tree tests pass. Canvas transport/native PNG and both delivery milestones remain open. See [evidence](research/evidence/native-primary-extent-2026-10-10.json) and [scope](docs/reverse-engineering/2026-10-10-native-primary-extent.md).

## 2026-10-10 — Extent CLI verifier and observation failures

Implemented frozen source-frame CLI versus full native extent consumer, independently projected/decoded PNGs, transparent holdouts and corruption/failure controls. Three attempts stopped on bounded process-observation timeouts; no full corpus acceptance. Fixed timeout retention and scoped owned-command identity reads; reused/start-changed identities still excluded. Nine targeted tests and all 323 isolated repository tests pass. Retained failures and public libproc observer next task: [dossier](docs/reverse-engineering/2026-10-10-extent-cli-observation.md). Both milestones remain open.

## 2026-10-10: canonical live-swap graph binding

Registered the fixed live_swap adapter, predeclared eight checks and bounded one-round graph binding. Owned run 20261011T034242Z-primary-live-wasm-swap-6ce0ce0b passed 84 full independent frames (1,376,256 bytes), 80 reused native allocations (1,310,720 bytes), six failed proposals, four close controls, five source rejections, three accepted source revisions and zero workers. Fresh-process verification and separate full-byte comparisons passed. Successful research is skipped through the sealed ledger overlay; scientific delivery and both milestones remain pending. Xcode bridge remains offline; no UI workspace opened. See research/evidence/live-swap-binding-2026-10-10.json.

## 2026-10-10: reentrant publication guard closure

Two owned controls reproduced a closed host publishing a stale snapshot and advancing revision. Added a synchronous closed-state recheck after invoking the guard and before mutation. Both controls now retain null closed snapshots and unchanged revisions; false/throw/promise guards preserve the complete last-good allocation. Expanded canonical live-swap checks pass in 20261011T035112Z-primary-live-wasm-swap-8279b44a with separate full-byte checks over 84 independent and80 reused-native allocations. Six host/source/corpus regression tests pass. Failure/fix sources and results sealed in research/evidence/live-guard-reentrancy-2026-10-10. Native Canvas and scientific delivery acceptance remain pending.

## 2026-10-10: bounded owned source-file loop

Implemented actual finite file polling, hash deduplication, latest pending-source coalescing, invalid/deleted-source ticket invalidation and cooperative builder closure/deadline abort. Three source revisions and seven edit/retention/close controls pass against pinned prebuilt modules, with one explicit closure abort and one automatic deadline abort. Expanded canonical frozen run 20261011T040407Z-primary-live-wasm-swap-6a7fe1c3 passes sixteen declared checks; full84 independent/80 reused-native allocations and saved watcher allocation compare exactly. Retained first test race failure and fixed settled-state control. This is a prebuilt fixture builder; fresh compiler/process-tree integration remains next. Native Canvas and scientific delivery remain open.

## 2026-10-10: fresh owned compiler file-loop adapter

Implemented a frozen-CLI subprocess builder with source/module/full-allocation receipt checks, bounded output and POSIX inherited-group timeout/abort. Two independent output roots freshly compile three supported file edits each with zero cache hits, exact pinned modules and98,304 checked frame bytes total; unsupported edits retain last good state. Controlled fork children start, receive group termination and cannot perform scheduled late writes after timeout or abort. Expanded canonical 20261011T041411Z-primary-live-wasm-swap-7262bae5 passes21 checks and full84 independent/80 reused-native allocations. Arbitrary escaping descendants and leader-exit orphan accounting remain unaccepted. Native Canvas policy and scientific delivery remain open.

## 2026-10-10: anchored compiler orphan cleanup

Retained two actual failures where compiler target exits0/7 but its inherited child writes late and defeats a200ms deadline. Private POSIX supervisor now remains group leader until target status is delivered on a separate descriptor, then the caller drains the still-owned group. Both fixed controls suppress late writes, settle near100ms and preserve target status0/7 separately from anchor termination. Canonical 20261011T042223Z-primary-live-wasm-swap-ddcf94bc passes23 declared checks, repeats fresh compilation and full84 independent/80 reused-native allocations. Escaping children remain excluded; native Canvas lifecycle and scientific delivery remain pending.


## Owned escaping-child controls (2026-10-10)

Four owned setsid/reparenting controls plus a frozen replay distinguish inherited-group cleanup from explicit public full-identity descendant drain. Group-only targets0/7 retain late writes; observed descendants produce no late writes and preserve both statuses. Three identity-selector mutants receive no signal; five receipt corruptions reject. Clean candidate archive:27 relevant tests pass. Evidence: `research/evidence/owned-escape-2026-10-10/manifest.json` (92c1c3a3f8156131a93fb18272377f9369a26fce3080b1c89be006934d509ac0). Detached cleanup is not yet integrated into the shipped Node runner. Unseen escapes and observation-to-signal races remain excluded. Native Canvas and scientific/delivery acceptance remain open.


## Nonblocking regular source gate (2026-10-10)

Retained prior FIFO deadline failure; regular/nonblocking/no-follow open and descriptor recheck now reject nonregular and replaced source nodes. Seven actual filesystem controls, four resealed false-claim rejections, and30 clean candidate tests pass. Canonical run20261011T044308Z-primary-live-wasm-swap-027f20a9 passes26 checks including existing full native/independent allocation comparisons and fresh builds. Manifest50a679dae2cfe22b88aef573bc9604c35e44196bfea1e585ca19ac4764367d06; independent before/fix evidence9d66780eee61887bae4222643c6d098961e49fa415c4e8d79d433af0801c0f8a. Owned local POSIX scope; Windows/arbitrary filesystem latency, native Canvas, and scientific/delivery acceptance stay open.


## Explicit observed compiler drain (2026-10-10)

Optional pinned public macOS observer path now tracks sampled full-identity escaping children and coordinates drain before inherited-group retirement. Four actual success/failure/deadline/abort controls preserve wait status and prevent delayed writes;3 real fresh compiler allocations match49152 independent bytes. Four resealed cleanup/status/tail mutants reject. Canonical run20261011T045341Z-primary-live-wasm-swap-9a8e2b5f passes30 checks;32 clean candidate tests pass. Canonical anchor9347f0aeac93b9e72774a5d774df14dcca52b52d843ffcd869d380534077c142; evidence6d5512f2b1c2eb2a63c78d6d44feb11eae14702f1a90dca3a27e57e668de02cd. Explicit macOS observer dependency; default group-only path stays available. Unseen escapes, observation-to-signal race, native Canvas and scientific/delivery acceptance remain open.


## Private supervisor input isolation (2026-10-10)

A further actual EOF control found the target inherited the supervisor nonblocking abort-read pipe and exited1 with BlockingIOError. DEVNULL target stdin now isolates private commands; owned read returns EOF/status0. Before/fix evidencec228964baff9ee05c4a36d09647100dddb080ec0a37e8eca40b7e56494eb2420 retains the initial incorrect deadline prediction and corrected EAGAIN diagnosis. Canonical run20261011T045810Z-primary-live-wasm-swap-69015bde passes31 checks, anchor25f3808fa9237a8fb1774831d7eb85c268997b40ee338a68cd94443c6557d254.33 isolated candidate tests pass; false resealed EOF claim rejects. Native Canvas/scientific acceptance remains open.


## Observer-loss and output-pressure controls (2026-10-10)

Two actual owned controls separate bounded pipe settlement from descendant release. Invalidated private helper reports drain unknown/false; escaped child retains stdout until emergency closure5506ms and later writes retained marker. Valid helper output pressure requests private abort and drains at258ms; no delayed write. Explicit emergencyClosed receipt now prevents accounting ambiguity. Four resealed false-claim controls reject;35 clean candidate tests pass. Canonical run20261011T050401Z-primary-live-wasm-swap-e9f4af29 passes34 checks, anchor600c6a736b2f1dce995e51c5f49feb7b420affc4522bff10d71ef551c1bd927a; evidence8dc52716ac13db373a4ecd5cc97ca7ca2069c326ffea1e06e4245f4a4f765b55. Lost-observer failure retained. Native Canvas/scientific/delivery acceptance remains open.


## Owned observer schema gate (2026-10-10)

Three actual bounded malformed helper responses previously produced success-shaped cleanup. Strict whole-response schema now rejects null group, negative parent, invalid microseconds and missing group before signalling; unknown target status remains unknown. Four before/after controls and three resealed false claims retained;38 isolated candidate tests pass. Canonical20261011T051314Z-primary-live-wasm-swap-037dbb3f passes35 checks, anchor6f626a8addf05e486982b949419888e1b81199b97629eb1d55a822f2eb07de59; evidence29bfaf86b71851d365f61dd962d5b9cbfde7dadfe884d3594c0a7c8da9c51146. Parser validation is not native identity authenticity or Canvas protocol acceptance. Both milestones remain open.


## Owned terminal envelope and reparent cancellation (2026-10-10)

Four malformed/truncated private terminal envelopes previously resolved. Exact receipt validation and received-trailer check now reject; valid fixture remains accepted. Actual full-identity reparent observation after parent exit0 triggers caller cancellation while drain completes: publication rejects, receipt separately preserves drained=true/remaining0 and no delayed writer. Five protocol fixtures plus one public libproc control; four resealed false claims reject. First helper reuse failed execute-mode prerequisite; byte-identical private executable copy repairs the harness, failures retained.40 isolated candidate tests pass. Canonical20261011T052359Z-primary-live-wasm-swap-587953a1 passes38 checks, anchor3c9d29ad2669e7e7911a505d676570039cba66089d21ff0a1744c854111ed78c; evidence77d4f5e8e4d2d86f983a95c4fd9fb8986d6c96f6b8ce7a46e40b562d966123db. No native Canvas protocol/release acceptance; both milestones remain open.


## Owned private UTF8 framing (2026-10-10)

Native pipe split across é previously corrupts accepted scope; invalid UTF8 also resolves. Fatal incremental decoding preserves exact split bytes, rejects invalid encoding and preserves bytewise ASCII. Three before/after owned supervisor controls reconstruct every paired emitted payload byte; three resealed false scope/acceptance/payload claims reject.42 isolated candidate tests pass. Canonical20261011T053325Z-primary-live-wasm-swap-a527ee66 passes41 checks, anchor344f618b2de704eab69747a50cee2b250ce1894022b94296ff48223f61fec96a; evidence505dc6a4bacf59d8d3c991db5c71a54ce0daf18a66cc80065fd61b47f081ffcc. These fixtures launch no compiler target and do not establish native Canvas transport. Installed Rust/cargo1.97.1 discovered at~/.cargo/bin despite absent shell PATH; next independent implementation is bounded frame ABI validation in Rust. Both milestones remain open.


## Dependency-free Rust frame core (2026-10-10)

New Cargo workspace/core validates the measured owned frame ABI, overflow-safe span/rendered count, complete16384-byte allocations and failure-preserving owned snapshots.84 accepted inputs compare1376256 bytes, including80 native-reference allocations and4 independently modeled inputs;10 negative controls reject pixel/padding/tail and7 ABI faults.5 Rust and45 Python tests pass in an isolated archive. First frozen build failed because source inventory omitted.rs; minimal freeze extension repairs it and retains failure. Canonical20261011T054612Z-primary-live-wasm-swap-8bf714d9 passes46 checks, anchord7b4f3bea4d5ad0d426c64873468c3182d4a4bacfcf9d4a67f08785b50a08f60; evidencec363bfba29756badca60ea288c72c8cb5a3b98c12002a8036a1df6edb937b968. No Rust rendering/WASM execution or cross-platform/native Canvas acceptance claimed. Both milestones remain open.


## Independent Rust primary rendering (2026-10-10)

Rust integer renderer now produces84 complete allocations (1376256 bytes), matching pinned Fraction predictions and80 public native references (1310720 bytes). Scope: three sRGB primary layers, alpha eighths, two orders, bounded dimensions/stride, A5 padding/C3 tail. Five invalid configuration CLI controls preserve owned output sentinels;7 Rust tests verify full invalid-buffer preservation and transparent/opaque order controls.3 resealed false pixel/tail/failure claims reject.47 Python plus7 Rust tests pass in an isolated archive (54 total). Canonical20261011T055326Z-primary-live-wasm-swap-2866b28f passes51 checks, anchor51890d87226c81d7940991d94b66e779ea3034598df24247cff86880d08af650; evidenceabccbd2eb05d61a170b9c7c901c7e6a0bf9c4fbe21b2ecfdb543f79369e4d219. Rustc has wasm32-wasip1/2 installed; next is an import-free no_std wrapper with actual runtime/full-allocation checks. No Swift source compiler, WASM execution, broader SwiftUI or platform/native Canvas acceptance claimed. Both milestones remain open.


## Rust import-free WASM execution (2026-10-10)

Allocation-free Rust contract separated from host FrameStore; no_std wrapper compiles with existing wasm32-wasip1. Actual modules export only memory/capacity/pixels/render and import nothing.84 macOS V8 executions compare1376256 complete bytes against independent Fraction expectations and1310720 public native reference bytes.336 invalid strides preserve complete allocations;84 memory growth attempts reject; resealed false padding, export ABI and cleanup claims reject.49 Python and7 Rust checks pass in isolated archive. Canonical20261011T060503Z-primary-live-wasm-swap-5cb279d3 passes56 checks; anchor7ed5fa5bd1ae76a7ecdc85e1842a101af3ea291414b7f3ac34560f5943243855; evidence07b13e3e2c7cc113a336b7e401867c75aa72aa70069d52572a4657a9224e2039. This is configuration-derived owned Rust WASM, not a Swift compiler or browser/Linux/Windows acceptance. Both milestones and native Canvas protocol/final-release/capture gates remain open. No bridge restart or owned Xcode workspace.


## Rust independent WASM interpreter (2026-10-10)

WasmKit executes26 original Rust modules capacity/pixels and42 actual render receipts.42 instrumented Rust checker modules each execute5 controls in WasmKit and V8: full independent allocation, visible-byte corruption, padding-or-visible corruption, last-byte corruption, invalid-stride preservation.210 full comparisons cover3440640 bytes per engine, detecting126 single-byte faults; separate V8 reader inspects every actual allocation byte.3 resealed false result/native/checker claims reject.51 Python plus7 Rust tests pass in isolated archive. Canonical20261011T061257Z-primary-live-wasm-swap-1defb692 passes62 checks; anchor9bfac1eb27ca44089e0e644b0712cb94c77bbc7c18457e2aa868bb8abf89d6bc; evidenceb87c189e9b714ddbb159c76bbb8caca55f9bd2bea4f0510b28324c110224c522. Both runtimes execute on macOS; instrumented checker exports verify in addition to original ABI. No non-Apple/browser or native Canvas transport/release/capture acceptance. Both milestones open.

Independent Rust second-runtime reader additionally reruns94 original capacity/pointer/render receipts; a fourth resealed false capacity claim rejects. Targeted fresh archive reader tests pass; original58-test candidate archive remains verified.


## Finite source to Rust WASM live revisions (2026-10-10)

Three supported primary expressions now lower into trusted Rust no_std kernels, compile through a pinned actual Rust compiler and publish3 live source revisions/49152 exact independent bytes. Observed ancestry drains compiler/linker controls; unsupported source target2 retains revision3 and live frame.26 actual CLI prebuild rejections cover22 grammar controls, compiler-pin mismatch, oversized input, FIFO and symlink; no output directory created.3 resealed false padding/compiler/drain claims reject.53 Python plus7 Rust tests pass in isolated archive. Canonical20261011T062316Z-primary-live-wasm-swap-83823ea7 passes68 checks; anchor6d51d711deb3a5d01c8a565b4b22b7e8286344c980e4b175bbc149861a922bfc; evidence7cf8a0b11b90f5f479e8409ba909a160ab77c738a88804b9ab5724ac0a631382. Finite expression lowering, not general Swift compilation; no non-Apple/browser/native Canvas acceptance. Both milestones open; bridge offline, no restart/workspace.


## Actual Rust compiler failure/recovery (2026-10-10)

Owned actual Rust compiler identity observed before abort and300ms deadline; both exit-15, observed ancestry drains, no artifact appears during350ms late-write check. Successful stale target exits0 but ticket rejects; all3 controls retain49152 exact prior live frame bytes. Normal compile recovers revision2 and zero workers.3 resealed false wait/late/padding claims reject.55 Python plus7 Rust tests pass in isolated archive. Canonical20261011T063558Z-primary-live-wasm-swap-803a7d05 passes73 checks; anchorbd74b13116194130de09380fc44ceeb7649b0b231d3efacedb02463abc6ca1a1; evidence7cf4104e2fc7ac1774c4bd26cb0e8f44ee548ad0f2320eafd18a5398669c916a. Failed manifest reader experiment retained, repaired with changed implementation; focused helper executable mode error retained. Stress workload includes6000 trusted exports to keep actual compiler running; not general Swift parsing or native Canvas release. Both milestones remain open.


## Rust target/linker pin and reusable builder (2026-10-10)

Source CLI now requires a pre/post target/linker inventory pin: 58 target files/102044269 bytes, actual compiler and2 installed linker files. Reusable Rust source builder drives3 fresh file-loop revisions/49152 exact bytes and unsupported-source retention. Actual false inventory pin exits2 before output creation. Fresh reader rehashes installed bytes and rejects4 resealed self-consistent false target/linker/missing-file/rejection claims.57 Python plus7 Rust tests pass in isolated archive. Canonical20261011T064553Z-primary-live-wasm-swap-7f4024f2 passes75 checks; anchordf89bf03bed3681c313a1bd461d766e225694bba82f89b928d2ee1e108ae1bd6; evidencee24ef02af66f6cd43054f41efcd1c6a00b2b52c9585b6dc8ea663bb01cc29557. Initial graph selection skipped submodule-only change until substantive freeze/pin assertions and predeclared checks were added; no experiment executed then. Full dynamic-library/OS dependency closure and both milestone contracts remain open.


## Actual Rust source-file generation and close controls (2026-10-10)

Actual compiler observation triggers a source-file replacement during generation2: generation2 compiles successfully but rejects stale ticket; generation3 publishes revision2. Close control captures valid revision1 immediately before close, aborts observed compiler with wait-15 and observed ancestry drain, then requires empty closed snapshot/zero workers/timers. Four full allocations/65536 bytes and four actual WASM artifacts independently checked. One cancelled artifact remains absent during250ms late-file check. Three resealed false generation/drain/padding mutants reject.59 Python plus7 Rust archive tests pass. Canonical20261011T065712Z-primary-live-wasm-swap-130284f8 passes79 checks; anchordac86949c448ad891744ede9bb40c39ef5eb1f70bf5654d64f10f2c533a68064; evidence7ff667137e0d61931b3ab872eff9f7fcbba64100dea161926988609f4ac4a4bb. Failed post-close retention expectation retained and corrected without changing host policy or expanding deadlines. Neither control identifies linker-phase cancellation or native Canvas semantics; both milestone contracts remain open.


## Actual file-loop failure retention and recovery (2026-10-11)

Rust builder now records post-execution validation errors with successful process receipt, and exposes a bounded50..5000ms deadline. Actual50ms source CLI deadline (phase unlocalized), wrong toolchain pin, and postcompile independent-oracle rejection each retain valid revision1 and recover revision2 after new source.3 controls/147456 allocation bytes and7 successful WASM artifacts independently checked;3 resealed false wait/recovery/padding mutants reject.61 Python plus7 Rust archive tests pass. Canonical20261011T070455Z-primary-live-wasm-swap-bd179a59 passes83 checks; anchor8abafb41f77ff03cadfcbcaae3983c7f66b9682833bd3882b1dbf198a556e48a; evidence4786db0da04c73e9a37307ce380f32fd4f4f27819424a0a1be45e1d888e4027f. Deadline does not identify linker phase; both milestone contracts remain open.


## Bounded Rust artifact descriptor gate (2026-10-11)

Rust builder replaces path-stat then unbounded path-read with nonblocking/no-follow opened descriptor read, capped1MiB, regular/nonempty validation, byte-count and pre/post identity checks, finally-close. Eight actual filesystem cases cover valid module, empty/oversize/directory/FIFO, open-time symlink swap, growth and same-size mtime mutation. Fresh reader reconstructs and replays all8;3 resealed false acceptance/descriptor/byte claims reject. Existing3 Rust source revisions still compare49152 bytes.63 Python plus7 Rust archive tests pass. Canonical20261011T091718Z-primary-live-wasm-swap-6b44cd8e passes86 checks; anchorfff6838c8b95b76266fa4b0dbe163424ffed0ef9aebb772c9f4e31a16319cd3e; evidenceab200f79b6e99d676886e1023da8a6b1d6d79cb11c15ba45db95631204009413. Worker module-name failure retained, repaired before changed focused/canonical execution. Final-component links only; general sandboxing, kernel reclamation and both milestone contracts remain open.


## Linker observation limit and retained artifacts (2026-10-11)

Two discriminating owned linker probes fail: first nonzero-wait expectation sees actual0 after abort-request path; changed verification then misses short-lived linker identity.25ms sampled ancestry cannot establish termination at observed phase. Runtime receipts were not written before assertions; retained evidence explicitly keeps that missingness. Fresh independent reader executes2 retained6000-export modules, checks32768 allocation bytes and12000 stress return values, rejects2 resealed false receipt/padding claims.65 Python plus7 Rust archive tests pass. Evidence1e98e86f9f39dc2e635f1f5480be1cce93c1ba7c6405fd0799830551e481a1f6. Failed experimental binding removed from active primary campaign; prototype now preserves attempts before assertions. Native cancellation acceptance remains open; retry requires changed observation method.


## Strict Rust receipt schema and byte identities (2026-10-11)

Builder bounds stdout receipt16KiB, validates exact root/config/source keys, lowercase SHA identities including actual module/generated/kernel bytes, finite dimensions/alpha eighths/reverse0/1, explicit target/cache/scope.3 actual receipts pass34 shape/pin mutants; independent Python schema and frozen JS replay agree,3 resealed false-validity/context/Boolean-reverse claims reject.3 live revisions/49152 bytes remain verified.67 Python plus7 Rust archive tests pass. Canonical20261011T093849Z-primary-live-wasm-swap-6bc05646 passes88 checks; anchora7be4b7c9d6e0aa1a0af7d151636335fe68418787e821d073323d304303f4c15; evidence22401f692b89dd4d98bb1cd9c69faad1cd78edb4a3b4e2d14f6755532c0b5a05. Initial Boolean reverse assumption failed and was corrected to measured numeric flag without changing frontend. Both milestone contracts remain open.


## Completed Rust builds and publication veto (2026-10-11)

Two deterministic owned file-loop controls close or supersede at external oracle callback after actual successful compilation and artifact/receipt validation. All5 subprocess target waits0/drained with no builder failures. Candidate generation2 publishes in neither case; supersession generation3 becomes revision2; closure clears live snapshot. Fresh independent V8 validates all5 modules and81920 complete allocation bytes including padding.3 resealed publication/wait/padding claims reject.69 Python plus7 Rust clean archive tests pass. Supplemental seal2d8617c26ad5075fffa1a8fc50e7083659f9ae399d8221a01029a275ef44566a; initial missing frozen cleanup helper failure sealedd235eccfe7474383422dec9a9ca047b5d369f42255f14ddb010c5fc56bde04cc; no execution deadline extended. This tests owned publication policy, not native cancellation timing or Canvas transport. Both milestones remain open.


## Bounded file-loop diagnostics (2026-10-11)

SourceFileLoop now retains latest64 events and reports dropped count plus detached latest/last failure. Error messages remove control characters and truncate at512 UTF8 bytes without splitting iteration code points.80 repeated owned fixture builder failures keep16384 frame bytes exact; invalid/deleted source classified; final64 events and100 dropped accounted. Independent frozen replay and3 resealed count/error/padding mutants pass.71 Python plus7 Rust archive tests pass. Sealb86e3d6ddbaa67c0e185254e44636d5ca1a42001eec7877ab9cf70e592c1176c. Before diagnostics method absent and unbounded event history; original source and TypeError retained. Prebuilt fixture evidence, not fresh compilation or native Canvas transport. Both milestones remain open.


## Local preview consumer contract (2026-10-11)

PreviewSession schema1 exposes start/poll/status/readFrame/close with bounded diagnostics and detached allocation/descriptor. Active WASM geometry now publishes atomically with frame/revision/source provenance. Actual Rust revisions13x7→9x5→13x7 pass8 consumer controls; unsupported edit exits2/drained and retains revision2 geometry/frame.3 fresh modules plus retained allocation yield65536 independently checked bytes;3 resealed geometry/hidden-failure/padding mutants reject.73 Python plus7 Rust clean archive tests pass. Seal5f4ae354812a9f4c4a35dcf1be81f022398e47ca813bf28ab4faff8689b70df9. Local module API only; no MCP transport, native Canvas or broad SwiftUI acceptance claimed. Both milestones remain open.


## Bounded owned preview channel (2026-10-11)

Owned NDJSON transport accepts exact id/method requests,4096-byte input,32768-byte response, one active plus one queued request, increasing IDs and close priority. Stop destroys owned input, drains session and operation, ends/destroys output; backpressure has50..1000ms write deadline.2 actual Rust frames13x7/9x5 carry32768 exact allocation bytes;9 fault controls and3 fresh independent stream replays pass.3 resealed queue/suppressed-reply/padding claims reject.75 Python plus7 Rust archive tests pass. Seal70d308a30ffa11267f7674b357f2dece0998f339aaabd4beb3a9e887a43e93b8. Initial syntax and immediate-next-request reply race retained/fixed; deadlines unchanged. Custom local transport, not MCP/native Canvas. Both milestones remain open.


## Owned stdin preview process (2026-10-11)

Custom preview_stdio process accepts operator-pinned compiler config, owned source and new build root; wire remains bounded NDJSON. Bounded independent Python primary-byte oracle handles supported finite expressions without fixture lookup. Actual process revisions13x7→11x6→13x7 recover after unsupported edit wait2;4 transported allocations65536 bytes exact. Separate EOF process suppresses pending reply, owned CLI wait-15/drained, phase unlocalized; both Node exits0 and zero workers/timers.6 fresh oracle replays and3 resealed exit/EOF-reply/padding faults pass.77 Python plus7 Rust archive tests pass. Seal026dfeb04cad4dd0115d531a7a6fc20658b5e1cbfb6330b888635c2998350aa7. Custom stdin integration, not MCP/native Canvas. Both milestones remain open.


## Owned MCP message handler (2026-10-11)

Custom NDJSON rejects MCP initialize, proving transport mismatch. Separate bounded PreviewMcp message handler implements pinned2025-11-25 negotiation/initialized/ping/tools and JSON-RPC versus tool errors; ID0/empty strings and opaque metadata supported. Independent fake-session controls compare32768 synthetic allocation bytes,9 malformed messages,256-ID bound,2 fresh Node replays and3 resealed faults.79 Python plus7 Rust clean archive tests. Seal26cf87d10dba2fd23cb63dfa298eef3364eb8098ccdfbc7428dc651464a9ea5d. Handler only: framing/EOF/cancellation/SDK/actual compiler integration remain open. Native capture bridge offline; both milestone contracts open.


## Bounded MCP stream controls (2026-10-11)

UTF-8/newline framing, serial queue8, bounded backpressure/EOF and optional cancellation implemented around PreviewMcp. Active tool cancellation closes owned session and suppresses pending reply; queued cancellation retains used ID. Ten cooperative fake-session stream controls,2 fresh Node replays,16384 independent synthetic bytes and3 resealed suppression/cleanup/allocation faults pass.81 Python plus7 Rust archive tests. Sealf47fb3de71f3ac8b34cc2332f3702f970cb66d6feaaed8db6bfe94f86b74f942. External stdio/actual compiler/SDK interop remains next; no native Canvas acceptance. Both milestone contracts open.


## Actual owned MCP stdio preview (2026-10-11)

Independent Python process client drives pinned MCP initialization/tools and actual Rust13x7→11x6→13x7 builds; unsupported CLI wait2 retains frame.65536 full allocation bytes,3 fresh modules and6 oracle controls pass. Four owned Node processes exit0/clean; early cancellation avoids build entry, entered cancellation and EOF record CLI wait-15/abort/drained with phase unlocalized. Four resealed exit/reply/wait/padding faults reject. Harness import and nested-manifest inventory errors retained and repaired without native reruns/deadline changes.83 Python plus7 Rust archive tests. Seal700c6bfe00763d9a5f54f450acc70444416755838185922e6c4deda87a71401e. Official SDK/full conformance/native Canvas acceptance remain open; both milestones open.


## Official MCP schema discriminator (2026-10-11)

Pinned official2025-11-25 schema falsifies7 unknown-ID id:null error responses; current handler/stream omit unreadable IDs and preserve known IDs.36 repaired owned envelopes plus specialized results/input schemas and16 actual MCP/Rust transcript envelopes validate. Reused native reader independently checks65536 full allocation bytes without native rerun. Three resealed ID/content/capability faults reject.85 Python plus7 Rust archive tests. Seale89f7262fde27c316fcf905a60e912d2ec2f2c8c77fcd2ab26404c09392a221c. Official SDK/full behavioral/native Canvas acceptance remain open; both milestones open.

### 2026-10-11: official MCP SDK interoperability

Official client2.3.1 explicit legacy handshake now accepts owned stdio preview edits/rejection/recovery/close and EOF cleanup.2 actual server waits0,4 fresh Rust/V8 modules,81,920 complete independently checked bytes;3 retained harness/prediction failures and3 resealed negative controls;87 Python+7 Rust isolated tests. [Evidence and scope](docs/reverse-engineering/2026-10-11-mcp-sdk.md). Modern protocol/full MCP/native Canvas and both delivery milestones remain open.

### 2026-10-11: explicit MCP frame availability

Owned handler0.2.0 now advertises typed availability and one structured allocation with a bounded reusable decoder. Official SDK/default AJV accepts initial/post-close unavailability, source edit/rejection/recovery and EOF cleanup;19 independently schema-checked replies,2 server waits0,4 Rust/V8 modules,81,920 full consumer bytes plus16,384 synthetic bytes. Duplicate-allocation cap failure retained/fixed without raising limits;8 decoder faults and3 resealed evidence faults reject;89 Python+7 Rust tests. [Scope/evidence](docs/reverse-engineering/2026-10-11-mcp-frame-contract.md). Both milestones and native Canvas acceptance stay open.

### 2026-10-11: current preview readiness and first-build recovery

Handler 0.2.1 reports current readiness without treating retained historical failures as current blockers. Official SDK controls first rejection/no frame, same-session recovery, unchanged poll without rebuild, stale-frame retention and second recovery/close. One actual server wait 0, two Rust/V8 modules, two expected CLI rejects wait 2,65,536 independently checked bytes; nine policy cases/three invalid cases and four correlated resealed faults;91 Python plus7 Rust tests. [Scope/evidence](docs/reverse-engineering/2026-10-11-mcp-readiness.md). Native Canvas refresh/transport and both milestones remain open.

### 2026-10-11: missing/empty source and exact restoration

Official SDK control retains full stale frames on missing/empty source and republishes identical source as new revision/generation after restoration. Three distinct successful Rust builds have identical module/image hashes; repeated invalid/valid polls add no events or builds. One actual server wait 0; 98,304 independent consumer bytes and three fresh V8 replays; four resealed faults reject; 93 Python plus seven Rust archive tests. [Scope and evidence](docs/reverse-engineering/2026-10-11-mcp-restore.md). Native Canvas reset/transport and both milestones remain open.

### 2026-10-11: explicit same-source refresh and retry

Handler 0.2.2 adds preview_refresh: unchanged poll skips rebuilding, explicit refresh republishes verified same source and retries unchanged rejected source. Last accepted frame survives both intentional failures; close rejects refresh. One actual SDK server wait 0, three successful Rust/V8 modules, two expected CLI waits 2, 98,304 independent consumer bytes; owned invalid/closed/concurrent/abort controls; four resealed faults; 95 Python plus seven Rust tests. [Scope and evidence](docs/reverse-engineering/2026-10-11-mcp-refresh.md). No user-state migration or native Canvas refresh/reset claim; both milestones remain open.

### 2026-10-11: correlated SDK consumer snapshots

Scoped JS consumer validates status/frame/status identity, retries one deliberately interleaved publication and preserves accepted state on eight hostile histories. One actual SDK server wait0, two Rust/V8 modules, one expected CLI wait2; 147,456 wire/snapshot bytes independently checked, four resealed faults; 97 Python plus seven Rust tests. Recorder alias and fixed deadline failures retained; reduced redundant recovery workload without raising limits. [Scope/evidence](docs/reverse-engineering/2026-10-11-mcp-consumer.md). Bracketed observation is not atomic/perpetual freshness or native Canvas protocol acceptance; both milestones remain open.

## 2026-10-11 — consumer terminal boundary

Fixed closed-with-frame and lifecycle revision contradictions after retaining old accepting controls. Valid terminal clears pixels and suppresses later RPC. Four fresh bounded Node replays, 65,536 complete allocation bytes independently checked, four resealed faults rejected. Harness path alias failure retained. See [evidence and scope](docs/reverse-engineering/2026-10-11-mcp-terminal.md). Native capture/release/reuse and both milestones remain open.

## 2026-10-11 — consumer diagnostic identity

Fixed four correlated published-diagnostic contradictions after retaining old accepting results. Valid stale-source and terminal behavior preserved. Four fresh bounded verification replays,131072 independent allocation bytes including padding/tail; four resealed faults and prior8 consumer/2 terminal guards checked. See [evidence and scope](docs/reverse-engineering/2026-10-11-mcp-identity.md). Native R1/R2/capture and both milestones stay open.

## 2026-10-11 — native two-queue generation fence

Two owned public Metal helpers pass: stale event2 completes reader with old frame while writer waits3; fresh event4 yields new frame. 229376 full allocation bytes independently checked, six resealed faults rejected; actual waits0, retained REA helper identity and tool-argument failure. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-queue-order.md). No Canvas/cross-process release acceptance; both milestones open.

## 2026-10-11 — native buffer object lifetime

Two owned Metal helpers measure CPU-owner drop retention in encoded-uncommitted and committed-timeout modes, then weak buffer/command nil after command disposal/pool drain.131072 full bytes independently checked, six resealed faults; actual waits0; REA identity retained/sessionclosed. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-buffer-release.md). Weak nil is not physical memory reclamation; Canvas/Mach release and both milestones remain open.

## 2026-10-11 — native owner attribution discriminator

Initial four-mode owner prediction failed: same-pool CPU-only/unencoded/unretained buffers also stayed weak alive. Failed controls sealed. Nested construction pool drain separates ownership: only retained-encoded buffer stays alive while command owner remains. Four native waits0,425984 full bytes independently checked, six resealed faults; REA bothhelperidentities/closed. See [scope and correction](docs/reverse-engineering/2026-10-11-gpu-buffer-owner.md). Same-pool liveness does not identify a sole owner; physical/Canvas/Mach release and both milestones remain open.

## 2026-10-11 — native submission and destruction callback distinction

Unsubmitted command destruction invokes its handler once with status0, contradicting the initial no-callback prediction (retained). Submitted default retained-reference work survives both CPU owner drops and construction pool drain, times out with zero callbacks, then explicitly released event completes once with status4. Four native waits0,196608 fullbytes, six resealed faults. Final weak command lifetime varies; no physical reclamation claim. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-submission-lifetime.md). R1/R2/Canvas and both milestones remain open.

## 2026-10-11 — queued-before-import surface failure

Four owned audited native peers discard one measured queued attachment by destroying its inbox without receive/import. COPY_SEND keeps senderref1; MOVE_SEND removes original sender name. Sender retained CF and replacement-port-only mutated storage remain exact after peer exit; endpoints and rendezvous removed, completion rejected.196608 fullbytes including padding/tail, seven resealed faults;REA identity/closed. See [scope and evidence](docs/reverse-engineering/2026-10-11-surface-queued-drop.md). No final physical reclamation/Canvas claim; both milestones open.

## 2026-10-11 — rejected coalesced descriptor cleanup

Four owned audited peers receive two coalesced IOSurface send descriptors in an intentionally invalid fixture envelope, reject without import and release refs2→0 via whole-message destruction or refs2→1→0 via explicit release/descriptor clearing/destruction. Sender retained CF and replacement-port-only storage remain exact through peer exit46.196608 fullbytes including padding/tail, seven resealed faults;REA identity/closed. See [scope](docs/reverse-engineering/2026-10-11-surface-rejected-envelope.md). No generic parser/Canvas/physical release claim; both milestones open.

## 2026-10-11 — consumer close revision monotonicity

Old correlated closed revisions0/1 after published2 discarded the accepted frame and terminally ignored restored-ready replies. Fixed lifecycle revision guard rejects stale close, retains wholeframe and recovers; valid stale/closed2 unchanged. Baseline contradiction retained,163840 independent completebytes,5 resealed faults. Fresh Node fixture control using historical SDK packets, no new native/SDK capture. See [scope](docs/reverse-engineering/2026-10-11-mcp-close-revision.md). Both milestones and native gates remain open.

## 2026-10-11 — public shared-event carrier distinction

Ordinary secure handle archive fails with no data/error4866 while secure string succeeds. Corrected same-process anonymous NSXPC reconstructs shared value3; independent event99 leaves it3; imported event7 releases owned gated work with one completed4 callback. Four native waits0,131072 full saved bytes, seven resealed faults. Initial observer limitations/prediction retained. Cross-process ownership and Canvas remain open. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-event-carrier.md).

## 2026-10-11 — owned cross-process shared event

Separate owned typed XPC peer signals shared event7 and releases sender GPU work; wrong-event-only99 leaves shared3 and another20ms timeout/zero callbacks until explicit sender7. Four parent waits0/peer exit0 and removed transient services; distinct public connection PIDs correlate.131072 fullbytes, ten resealed identity/exit/cleanup/order/padding faults. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-event-peer.md). R1/R2/R3/Canvas and both milestones remain open.

## 2026-10-11 — peer loss versus completion dependency

Deliberate owned peer exits47 before signal and48 after signal both yield null reply/error4097; before remains event3/pending zero callbacks, after preserves event7. Explicit sender release then completes4/exact bytes. Four parent waits0, deliberate peer exits retained, four transient services removed113;131072 fullbytes/eleven resealed faults. Connection PID0 after loss is not live peer identity. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-event-failure.md). Both milestones and R1/R2/R3/Canvas remain open.

## 2026-10-11 — retained event across local connection invalidation

After first connection invalidation and original sender-variable drops, same peer/same imported property token signals7 through new connection. Dropped property instead leaves sender3/pending0callbacks; retained recoveryalias7 explicitly completes4/full bytes. Four parent waits0/peer exits0/services removed113;131072 fullbytes/eleven resealed faults. Recoveryalias/command retained; no sole-owner or physical release claim. See [scope and evidence](docs/reverse-engineering/2026-10-11-gpu-event-disconnect.md). Both milestones/R1/R2/R3/Canvas remain open.

## 2026-10-11 — live verification worker quarantine

Hung pixels live-read deadline previously left worker alive, then repeated timeout; baseline retained. Fix retires failed worker, preserves cached revision1 bytes, rejects repeat as unavailable and recovers healthy revision2; close quiescent. Four producer waits0,196608 fullbytes/seven resealed faults. Next readiness/consumer integration must distinguish cached frame from unavailable execution. See [scope](docs/reverse-engineering/2026-10-11-live-read-timeout.md). Both milestones/native Canvas remain open.

## 2026-10-11 — unavailable execution and cached consumer

Readiness now marks worker0 publication stale; existing consumer adopts two stable statuses with identical accepted bytes. Unchanged-source refresh recovers healthy revision2/generation2; close clears frame and stops RPC. Two successful producers plus two retained stride-contract fixture failures;98304 independently expected bytes and8 resealed faults. See [scope](docs/reverse-engineering/2026-10-11-mcp-quarantine.md). Owned handler policy only; native Canvas/both milestones remain open.

## 2026-10-11 — cached consumer adversarial histories

Two repeat14-history packet replays reject forged identities/rollback/diagnostics/unstable status/cold unavailable reads and accept stale cached status or bounded healthy retry. Lifecycle mutation remained rejected by rollback (prediction contradicted); diagnostic mutation exposed missing check and exited1. All786432 relevant bytes and8 resealed faults verified. [Scope](docs/reverse-engineering/2026-10-11-mcp-cache-guards.md). Historical owned packets only; both milestones/native capture remain open.

## 2026-10-11 — owned request-cap cleanup

At256 request IDs, baseline refused close while retaining worker1/timers2/frame. Handler now awaits owned close before limit error; fixed worker0/timers0/frame null, IDs remain256, throwing cleanup reports sanitized failure. Four waits0,98304 independently expected bytes/eight resealed faults. [Scope](docs/reverse-engineering/2026-10-11-mcp-request-cap.md). Owned handler policy only; native R1/R2/both milestones remain open.

## 2026-10-11 — channel cleanup outcome

Channel summary now separates transport closed from cleanup complete/failed. Actual owned worker controls distinguish throw before release(worker1) from throw after release(worker0); both failed adapters reported failed, all finally closed. Four waits0/12 controls,262144 independent bytes/eight resealed faults. [Scope](docs/reverse-engineering/2026-10-11-mcp-channel-cleanup.md). Non-settling close remains explicit; no SDK/native physical release/both milestone completion.

## 2026-10-11 — actual stdio cleanup failure exit

CLI previously exited0 despite channel cleanup failed. It now retains lifecycle artifact and emits sanitized cleanup-failed/exit3; success stays0. Four actual owned Node processes with explicit compiler fixture/post-release failure injection,65536 independent bytes/seven resealed faults. [Scope](docs/reverse-engineering/2026-10-11-mcp-stdio-exit.md). No Rust/SDK/native compiler claim; nonsettling close and both milestones remain open.

## 2026-10-11 — asynchronous CLI shutdown watchdog

Baseline hung close required owned parent kill/reap after5sec(-9). CLI now keeps requested deadline+1000ms watchdog, retains pre-exit worker1/timers2/cleanupunknown and self-exits4; positive exit0 and prior rejection exit3 verified. Four actual Node processes,65536 independent bytes/eight resealed faults. [Scope](docs/reverse-engineering/2026-10-11-mcp-shutdown-watchdog.md). Event-loop timer only; external deadlines/native/both milestone acceptance remain.

## 2026-10-11 — native syntax whitespace discrimination

Four owned Swift frontend processes accept space/VT/FF/CR at Color-opening boundary for both custom subsets; all eight lowerer configurations agree. Proposed VT/FF rejection hypothesis contradicted; no grammar fix warranted. Actual waits0/no timeout/diagnostic; independent source/identity reader, seven resealed faults, current lowerer regressions. [Scope](docs/reverse-engineering/2026-10-11-source-whitespace.md). Native syntax only; both milestones/Canvas gates remain open.

## 2026-10-11 — native member-access syntax rejection

Native parser rejects space/tab/newline after member-access dot while both lowerers accepted. Tightened both grammars; preserved legal Color whitespace. Four waits0/1/1/1/no timeout, six invalid expressions now reject, independent source/diagnostic/identity reader and eight resealed faults. [Scope](docs/reverse-engineering/2026-10-11-source-dot-spacing.md). Native syntax only; both milestone/Canvas acceptance remain open.

## 2026-10-11 — cached-build CLI regular input gate

FIFO blocks old primary build CLI until owned parent1.5sec kill/reap; symlink target reaches parser. CLI now requires bounded ASCII POSIX regular descriptor/nonblocking/no-follow open and detects changed reads, closing descriptors. Four actual children;fixed rejects before build/cache with no timeout. Six resealed faults and actual descriptor/replacement/mutation controls. [Scope](docs/reverse-engineering/2026-10-11-source-cli-input.md). No compiler/render/native/platform acceptance;both milestones open.

## 2026-10-11 — bounded cache metadata reads

Baseline index FIFO hangs until owned2sec kill/reap; fixed index/manifest reads use bounded nonblocking/no-follow regular descriptors, reject without extra build/publication. Four producers include retained missing-source harness failure;baseline manifest not run. Explicit fake compiler,100 modulebytes/six resealed faults; no renderer/padding claim. [Scope](docs/reverse-engineering/2026-10-11-cache-input.md). Both milestones/Canvas remain open.

## 2026-10-11 — native external observed-model state

Same owned ImageRenderer updates red→blue immediately on external model mutation and blue→red on reset; fresh renderer retains same model value, fresh default model resets red. Two fresh native waits0/16 phases/262144 fullbytes incl1728padding/250624tail/eight resealed faults/zero appwindows. SDK compile failure retained within four-producer budget. [Scope](docs/reverse-engineering/2026-10-11-native-observed-state.md). No Button/@State/Canvas refresh/transport claim;both milestones open.

## 2026-10-11 — hidden native button input failure retained

Hidden owned SwiftUI host exposes AXGroup only in two runs;zero buttons/actions.32768 full initial-red bytes incl216padding/31328tail/eight resealed faults/zeroownwindows;protocol compile failure retained within four producers. [Scope](docs/reverse-engineering/2026-10-11-native-button-press.md). Input acceptance failed;next needs changed hosting visibility/lifecycle. Both milestones open.

## 2026-10-11 — visible native button discovery boundary

Ordering the owned host behind other windows changes visibility to true and preserves non-key status, but two public tree walks still expose AXGroup only and deliver zero actions. All 32,768 initial-red bytes, including padding and unused tail, are verified; ten resealed faults cover the evidence checks. Both owned windows close. [Scope and next prerequisite](docs/reverse-engineering/2026-10-11-native-button-visible.md). Both milestones remain open.

## 2026-10-11 — navigation and hit-test discovery boundary

Two owned SwiftUI probes expose no navigation children; public center hit-test returns AXGroup only and delivers zero actions. The screen point is [80, -62], so display placement remains unvalidated. Both owned windows close. All 32,768 initial-red bytes and thirteen resealed evidence faults are verified. [Scope and next prerequisites](docs/reverse-engineering/2026-10-11-native-button-hit.md). Both milestones remain open.

## 2026-10-11 — owned main-screen prerequisite failure

Two placement/control acquisitions fail at NSScreen.main with actual -5 waits and OwnedState Code=3. No input, result or frame was acquired; cleanup is unverified. Seven resealed false-acceptance corruptions are rejected. [Retained failure and retry prerequisite](docs/reverse-engineering/2026-10-11-native-button-placement.md). Switch to independent work while display availability remains unresolved. Both milestones remain open.

## 2026-10-11 — bounded cache payload entry reads

Baseline cached IR/WASM FIFO digest reads block; both owned children are killed and reaped at two seconds. Fixed entry reads enforce source/IR/module size caps and nonblocking/no-follow regular descriptors, compare the same bounded bytes, and preserve publication without extra fake stages. Four producer controls, 120 fake-module bytes and six resealed faults. [Scope](docs/reverse-engineering/2026-10-11-cache-payload.md). Both milestones remain open.

## 2026-10-11 — bounded compiler subprocess output

Build commands now use temporary output files and a child-only 4 MiB file cap, bounded diagnostic reads and explicit limit rejection. Four owned Python emitter controls observe baseline 8192 bytes/exit 0 versus fixed 4096 bytes/SIGXFSZ under reduced test caps; parent limits remain unchanged. All 24,576 diagnostic bytes and seven resealed faults verified. [Scope](docs/reverse-engineering/2026-10-11-compiler-output.md). Real compiler, threaded/Windows/descendant and native Canvas acceptance remain open.

## 2026-10-11 — real capped-build qualification

Real LLVM compilation succeeds under current child-only caps; repeat source hits cache without more compiler calls or pointer change. V8 matches 131,072 allocation bytes against independent literal and anchored 720-byte native prefix, including padding/tail and invalid-buffer preservation. WasmKit returns render size 720; memory acceptance remains separate. Eleven resealed faults. REA universal imports fail and are retained. [Scope](docs/reverse-engineering/2026-10-11-capped-build.md). Both milestones remain open.

## 2026-10-11 — compiler timeout process-group cleanup

Baseline compiler parent timeout leaves owned same-group child writing; fixed commands isolate a POSIX session and kill that group before rethrowing timeout. Direct parents are reaped and bounded heartbeat quiescence is observed. Four owned processes, 32 heartbeat bytes and eight resealed faults. [Scope](docs/reverse-engineering/2026-10-11-compiler-tree.md). Descendant reaping/physical release, escaped sessions and normal-success descendants remain separate; real build qualification under changed spawn boundary remains next. Both milestones open.

## 2026-10-11 — real isolated-session build holdout

Real LLVM stages under changed Popen/session boundary exit0 with owned group IDs equal spawnedPIDs; cache hit preserves pointer and skips recompilation. Native-backed holdout12 V8 allocations match all131072 bytes, including padding/tail and invalid-buffer preservation. WasmKit render720 result is separately scoped. Twelve resealed faults. [Scope](docs/reverse-engineering/2026-10-11-session-build.md). Both milestones remain open.

## 2026-10-11 — verified completed-research adoption

Default live-swap binding now reuses its existing registered runner. New explicit anchored adoption validates current task scope, prerequisites and a fresh frozen-run verifier before idempotent research acceptance. Matching canonical run passes all88 declared checks; default graph has no ready candidates, while delivery review and both milestones remain open. API rejection controls and nine resealed false-promotion faults pass. [Scope and next prerequisites](docs/reverse-engineering/2026-10-11-graph-adoption.md). No corpus producers rerun; unrelated staged work preserved.

## 2026-10-11 — full-allocation native handoff failures

Audited owned CPU Mach import-error and timeout controls now compare full IOSurface allocations, including previously unchecked tail. Four snapshots match 65,536 bytes, including 2,160 padding and 60,928 tail bytes; explicit release/owned timeout peer status and local name removal verified. Twelve resealed faults. [Scope](docs/reverse-engineering/2026-10-11-surface-full-failure.md). R1 physical reclamation and native Canvas transport remain open. Independent native work remains available despite empty default graph frontier.

## 2026-10-11 — full-allocation delayed reuse contrast

Reused first handle sees updated image and generation-changing tail marker; separate first storage preserves prior frame. Ten snapshots match 163,840 allocation bytes including 5,400 padding and 152,320 tail bytes. Right/alias/lookup/peer cleanup observations pass; numeric global surface ID recurs across distinct fixture lifetimes. Fourteen resealed faults. [Scope](docs/reverse-engineering/2026-10-11-surface-full-reuse.md). Physical reclamation and native Canvas protocol remain open.

## 2026-10-11 — stale global surface ID contrast

Two released controls show IOSurfaceLookup(old_id) resolving replacement seed50 image/tail after old ID disappearance; held Mach right preserves original seed49 through 64 owned creations. All 73 allocations compare 1,196,032 bytes including row padding and unused tail; fourteen resealed faults pass. Explicit right cleanup and bounded lookup follow-up observed. [Scope](docs/reverse-engineering/2026-10-11-surface-global-id.md). Global IDs are not lifetime/frame versions; physical reclamation and native Canvas wire remain open.

## 2026-10-11 — remote CF alias release contrast

Audited remote CF alias preserves original after parent CF/right release and peer resource-name removal through 64 owned creations. Clean CF release and owned peer SIGKILL each yield null global lookup then numeric-ID recurrence resolving replacement bytes. All 140 full allocations compare 2,293,760 bytes including padding/tail; seventeen resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-remote-surface-alias.md). Physical reclamation and Canvas protocol remain open.

## 2026-10-11 — cross-task use-count cleanup

Remote explicit use count makes global in-use true while parent local count is zero. Clean decrement and owned peer SIGKILL both preserve parent contribution; final parent decrement clears global in-use. All 15 allocations compare 245,760 bytes including padding/tail; nineteen resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-remote-surface-use.md). Physical reclamation and Canvas completion remain open; approved capture broker socket still absent.

## 2026-10-11 — same-task alias use-count sharing

Three distinct CF wrappers share usage state: cross-alias increments/decrements yield repeated 0/1/2/1/1/0/0 trace; wrapper release preserves remaining contribution. All 34 full allocations compare 557,056 bytes including padding/tail; seventeen resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-surface-alias-use.md). Physical reclaim and Canvas generations remain open.

## 2026-10-11 — public content seed versus full bytes

Write lock already returns next seed; no-op write changes seed without byte changes. Active/padding/tail edits and exact restoration preserve resource ID and alias agreement. All 28 allocations compare 458,752 bytes; eighteen resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-surface-content-seed.md). Returned seed is not byte hash or recovered Canvas generation; internal update timing remains open.

## 2026-10-11 — seed visibility inside CPU lock

Both distinct same-task aliases observe advanced seed before content edit or unlock; full in-lock before/after bytes discriminate edit timing. All 52 allocations compare 851,968 bytes; twenty-three resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-surface-seed-timing.md). Cross-task visibility, synchronization and Canvas completion remain open.

## 2026-10-11 — remote seed/read-lock visibility

Audited peer read-only lock succeeds while parent write access stays held. Remote seed 2 precedes edit and accompanies both old and changed bytes before unlock. Two peer controls compare all 20 allocations/327,680 bytes; twenty-two resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-remote-surface-seed.md). Controlled parent pauses preserve distinct concurrency/GPU/Canvas completion unknowns.

## 2026-10-11 — owned stream-close failure cleanup

New fixture retires FILE pointer before fclose. Owned ENOSPC close callback runs once, closes fd, releases CF, suppresses completion and exits 42; parent records bounded Mach timeout and cleanup. All 20 allocations/327,680 bytes compare; twenty-eight resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-surface-stream-close.md). Historical evidence preserved; filesystem generality and actual Canvas errors remain open.

## 2026-10-11 — compiler success descendant counterexample

Actual run_compiler returns root 0 while owned finite child grows heartbeat 1→7→24 bytes. One qualified control, initial harness failure retained, four producers total and no kill. All 56 controlled bytes and twelve resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-compiler-success-descendant.md). Normal-success process-tree quiescence remains build acceptance work; no published artifact corruption claimed.

## 2026-10-11 — conservative compiler success admission

Production compiler boundary rejects residual process group after root 0 using read-only signal 0; clean Python and actual clang compile still pass. Owned finite child self-exits; all 32 controlled bytes/twelve resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-compiler-success-admission.md). Guard prevents known same-group success admission; escaped descendants and actual WASM build qualification remain open.

## 2026-10-11 — real WASM success admission qualification

Two real LLVM stages pass signal-0 group absence checks; identical source cache hit skips compilation and preserves pointer. V8 all 131,072 bytes match native-backed expectations, WasmKit returns 720 separately; fifteen resealed faults pass. Historical test coupling failure retained and source hash pinned. [Scope](docs/reverse-engineering/2026-10-11-admitted-build.md). Escaped descendants and native Canvas remain open.

## 2026-10-11 — explicit compiler ancestry admission

Opt-in read-only ancestry witness added. Group-only control misses finite setsid child. Native observer catches launcher→app transition but initially rejects too early; failure retained, root refresh repaired with finite semantic tests. All 100 controlled bytes and ten resealed faults pass. [Scope](docs/reverse-engineering/2026-10-11-compiler-observed-admission.md). Post-fix native admission remains unqualified; no budget replenishment or user observer edits.

## 2026-10-11 — observer qualification failure accounting

Native observer fails live-root read; existing cleanup signal denied. Both failures retained, no bypass or retry. Production exception path now always attempts bounded root wait and preserves original failure with cleanup notes; independent controlled denial and clean-root checks pass all 57 bytes/ten resealed faults. [Scope](docs/reverse-engineering/2026-10-11-compiler-qualification-cleanup.md). Native observer/cold build qualification remains open.

## 2026-10-11 — stable-phase observer diagnosis

Four stable owned snapshots match independent parent/group/dyld paths; acknowledged child Popen/runtime PID agree, exit 0 and marker bytes pass. Thirteen resealed faults reject wrong identity/availability. [Scope](docs/reverse-engineering/2026-10-11-observer-stable-diagnostic.md). Earlier startup failure and signal permission remain unresolved; no compiler retry or signals.

## 2026-10-11 — native ready-gated ancestry admission

Actual root 0 is rejected while observed same-identity detached child remains live after reparenting; clean ready root admits. Known child self-exits and bounded retirement read sees no live lifetime. All 76 retained bytes/fourteen resealed faults pass; no destructive signals. [Scope](docs/reverse-engineering/2026-10-11-observer-ready-admission.md). Explicit owned readiness only; generic startup/LLVM observer/Canvas remain open.


### 2026-10-11 explicit observer active-root coverage

Fixed optional compiler witness accepting omitted/unrelated-only active-root snapshots after prior observation. Six deterministic source controls and seven resealed faults; fake process verifies exception cleanup/reap without native launch or signals. Historical ready-gated native evidence stays frozen. Final known-descendant absence, generic startup, LLVM observer and Canvas gates remain open. See docs/reverse-engineering/2026-10-11-compiler-observer-completeness.md.


### 2026-10-11 final compiler descendant retirement

Fixed optional observer admitting missing final known children as implicit retirement. Twelve source controls, eight resealed faults and wrapper rejection without native signals; matching zombie row remains accepted under scoped process policy. Historical native evidence stays frozen; native zombie/absence/LLVM and Canvas acceptance remain open. See docs/reverse-engineering/2026-10-11-compiler-descendant-retirement.md.


### 2026-10-11 native zombie visibility

Pinned observer omits the same known child both during independently waitidWNOWAIT-proved unreaped exit42 and after waitpid reap42; live birth/path identity was present first. Parent0,32exactbytes,6nativeprocesses,0signals;12resealedfaults. Current backend does not qualify matching-zombie admission. See docs/reverse-engineering/2026-10-11-zombie-visibility.md.


### 2026-10-11 typed retirement observer counterexample

Added explicit bounded birth/state diagnostic adapter. Native live and birth-mismatch controls pass; unreaped/reaped both unavailable. Changed direct owning-parent BSD query returns136bytes live then0/0; prediction of recovered zombie visibility falsified.64exactbytes,16native,0signals,14resealedfaults; no compiler admission bypass. See docs/reverse-engineering/2026-10-11-typed-retirement.md.


### 2026-10-11 cooperative superseded build cancellation

Source loop now aborts obsolete cooperative builder on changed valid/invalid/missing input and forced refresh. Eight actual V8/file before/after controls preserve latest generation and retained frames; all16allocations/262144bytes including1344padding and254976tail pass;12resealedfaults. Final workers/timers zero. See docs/reverse-engineering/2026-10-11-superseded-build-cancel.md.


### 2026-10-11 reentrant abort-close ordering

Source observation now respects synchronous close from cooperative builder abort callback. Eight actual V8/file controls reproduce prior shutdown error and verify fixed drain,1abort2builders0workers/timers. Eight baselineallocations131072bytes including672padding127488tail compare;13resealedfaults. See docs/reverse-engineering/2026-10-11-abort-close-reentry.md.


### 2026-10-11 actual owned builder cancellation and recovery

Actual live Rustc generation2 superseded through SourceFileLoop/RustSourceBuilder; owned CLI wait-15 and sampled abort/drain receipt pass. Fresh generation1/3 builds publish,2rejects; three allocations49152bytes including252padding47808tail match. Final workers/timers zero;18resealedfaults. See docs/reverse-engineering/2026-10-11-actual-builder-cancel.md.


### 2026-10-11 cancelled builder entry before staging

Already-aborted Rust builder requests now reject before per-job directory/source creation. Eight actual JS/filesystem controls show4oldstages808bytes versus0fixed;2noncancelledhandoffs still reach interceptedspawn. Six sourcecopies1212exactbytes,12resealedfaults,0Nativejobs. See docs/reverse-engineering/2026-10-11-preabort-build-staging.md.


### 2026-10-11 bounded retained build history

Rust builder metadata now retains newest64 entries by default, configurable1–256, with dropped counts.280synthetic-boundary requests verify default/configured64/4, all140failureartifacts retained;invalidlimits create no root;12resealedfaults.0Nativecompilerjobs; rawdisk/per-entrybytes remain open. See docs/reverse-engineering/2026-10-11-bounded-build-history.md.


### 2026-10-11 per-builder stage allocation budget

Rust builder now limits newly allocated stages,default64/configurable1–256. Configured2stage control rejects third and repeated requests before handoff;preabort charges0. Five failurefiles/1010sourcebytes and12sentinelbytes preserved;12resealedfaults.0Nativecompilerjobs; byte/global quotas remain open. See docs/reverse-engineering/2026-10-11-build-stage-budget.md.


### 2026-10-11 native view-owned State binding

Captured public binding mutates held ImageRenderer privateState immediately;fresh samecontent renderer starts red whileoriginal stays blue;heldbinding reset restores. TwoNativeAA processes/18allocations294912bytes including1944padding281952tail pass;15resealedfaults;zeroownedwindows. No UI-event/Canvas reset claim. See docs/reverse-engineering/2026-10-11-native-state-binding.md.


### 2026-10-11 native content identity and State

Same-renderer same-id content preserves blue State; changing child id resets red, returning id resets again; detached old binding getter changes leave replacement red. Two native processes/22alloc360448bytes including2376padding344608tail;15resealedfaults;wait0/zeroownedwindows. Public ImageRenderer reference only, Canvas/source-edit migration remains open. See docs/reverse-engineering/2026-10-11-native-state-identity.md.


### 2026-10-11 native content parameter State preservation

Changed palette under fixed child identity refreshes pixels while retaining private State; original held binding changes alternate palette, original content restoration stays blue, changed identity resets red. Two nativeAA processes/22alloc360448bytes/2376padding344608tail;15resealedfaults;wait0/windows0. ImageRenderer reference only, no Canvas/source-edit migration claim. See docs/reverse-engineering/2026-10-11-native-state-content.md.


### 2026-10-12 native geometry update and State

Fixed-id frame input changes callback/context17×9→11×5→17×9 while privateState and original held binding persist;idchange resetsred. TwoNativeAA processes/22alloc360448bytes/2952padding347168tail;18resealedfaults;wait0/windows0. Owned public ImageRenderer reference, no Canvas/source-edit migration claim. See docs/reverse-engineering/2026-10-12-native-state-geometry.md.


### 2026-10-12 builder deadline validation ordering

Invalid timeout now rejects before artifact root creation.34actualNode/filesystem construction controls,14sentinels84bytes unchanged,valid50/5000/default pass,13resealedfaults,zero compilerjobs. Historical stage-budget evidence pinned independently. See docs/reverse-engineering/2026-10-12-build-deadline-validation.md.


### 2026-10-12 build failure persistence

Failure log write errors no longer mask original execution Error; separate persistence_error retained in memory.6actualNode controls with injected ENOSPC/EACCES,6sources1212bytes,15faults,zero actualcompilerjobs/oraclecalls. See docs/reverse-engineering/2026-10-12-build-failure-persistence.md.


### 2026-10-12 source staging failure retention

Source write moved inside builder failure handler;source failures retain originalError and chargedstage, double logfailure has separate persistence_error.8actualNode injectedcontrols,2sources404bytes,15faults,zero actualcompilerjobs. See docs/reverse-engineering/2026-10-12-source-stage-failure.md.


### 2026-10-12 retained build diagnostic byte bound

Error and persistence_error excerpts capped1024UTF8bytes at codepoint boundaries with originalbytecounts;caller originalError preserved.12actualNode injectedcontrols,12sources2424bytes,15faults,zero actualcompilerjobs. Totalrecord/diskquota remains separate. See docs/reverse-engineering/2026-10-12-build-diagnostic-bound.md.


### 2026-10-12 receipt/artifact rejection through reload

Sixactual builder/source-loop/V8 sequences with interceptedcompiler rejectgen2,retainbaseline/recovergen3,closeworkers/timers0.18wholealloc294912bytes/1512padding286848tail,16faults;0freshcompiler/nativeCanvas. See docs/reverse-engineering/2026-10-12-receipt-reload-rejection.md.


### 2026-10-12 failure record snapshot

Failure records JSONsnapshotted before caller mutation;cycle/BigInt/throwing getter produce boundedrecord_error without maskingoriginalError.10actualNode controls,10sources2020bytes,15faults,zero actualcompilerjobs;recordbytequota remains open. See docs/reverse-engineering/2026-10-12-failure-record-snapshot.md.


### 2026-10-12 retained failure record field cap

Serialized failure record field admits≤512KiB;oversize omits with originalbytecount/record_error whilecallerError/fullrecord preserved.10actualNode boundary/emoji/escapedNUL controls,10sources2020bytes,16faults,zero actualcompilerjobs. Initialheap/globalquotas remain separate. See docs/reverse-engineering/2026-10-12-failure-record-size.md.


### 2026-10-12 observation callback drain ordering

Synchronous callback errors requestabort and awaitcomplete beforeanchor release. Protocol before/after contrasts plus2nativeAA ownedrootcontrols actualwait−15/drainedremaining0;originalError retained;15faults. Sampledscope only. See docs/reverse-engineering/2026-10-12-observer-callback-drain.md.


### 2026-10-12 callback descendant actual wait

Acknowledgedsetsidchild callback abort:4actualnative controls parentwait43/childwait42 raw10752,drainedtracked2/remaining0,anchorSIGKILL.4peerfiles32bytes/16faults. Explicit childalarm added/requalified insecondpair within4slots;all retained. Sampledscope only. See docs/reverse-engineering/2026-10-12-callback-descendant-wait.md.


### 2026-10-12 malformed observation cleanup

Parserexception nowrequestsabort and awaitscomplete;2actualnative proxycontrols parentwait43/childwait42 raw10752/16peerbytes,drainedtracked2remaining0. Missingcomplete negative harddeadline rejects/reportnull/emergencyClosed;16faults/4slots. See docs/reverse-engineering/2026-10-12-malformed-control-drain.md.


### 2026-10-12 fatal UTF8 observation cleanup

Decoderfailure nowrequestsabort;2actualnative controls parentwait43/childwait42 raw10752/16peerbytes,TypeErrorcodepreserved/drainedtracked2remaining0. Missingcomplete negative rejects/reportnull/emergencyClosed;17faults/4slots. See docs/reverse-engineering/2026-10-12-utf8-control-drain.md.


### 2026-10-12 control/output quota cleanup

Controloverflow requestsabort withoutquotareset;2Native control cases keep reportnull/emergencyClosed butindependent parentwait43/childwait42. Stdout positive ≤65536 retainedbytes/validdrainreceipt.3peerfiles24bytes/18faults/4slots;clientcontrolreceipt remainsunqualified. See docs/reverse-engineering/2026-10-12-overflow-control-drain.md.


### 2026-10-12 stderr/mixed output cancellation

Exactstderr65536 admittedthenmanualabort;stderr65537 andaggregate32768stdout+32769stderr inbothorders cancel atcombinedlimit.4actualnative parentwait43/childwait42 raw10752/32peerbytes,18faults/4slots;no fixedchunk/encoding/Canvasclaim. See docs/reverse-engineering/2026-10-12-mixed-output-cancel.md.

### 2026-10-12: Unicode output accounting discriminator

[Finite source controls](docs/reverse-engineering/2026-10-12-unicode-output-accounting.md) distinguish raw-buffer quota from saved text:16 injected controls, exact/over-limit Unicode and split/invalid/NUL inputs.65,536 invalid bytes become196,608 UTF-8 text bytes; raw capture cannot be inferred from lossy strings.12 resealed faults; no native target launched. Next expose bounded raw-byte accounting. Both milestones remain open.

### 2026-10-12: retained raw-output accounting

[Production record fix](docs/reverse-engineering/2026-10-12-raw-output-accounting.md) exposes admitted stdout/stderr byte counts and SHA-256 before lossy text conversion.48 before/after injected controls,14 resealed faults;2,359,380 exact input bytes. No native target launched; historical native evidence remains frozen. Both milestones open.

### 2026-10-12: native raw-output accounting

[Actual owned controls](docs/reverse-engineering/2026-10-12-native-raw-output.md) verify Unicode/invalid/mixed raw counts and hashes through production supervisor cancellation.4actualparentwait43/childwait42,32exactpeerbytes;22resealedfaults. Text expansion stays distinct from original byte counts. No Canvas or unseen-escape claim; both milestones open.

### 2026-10-12: native failure versus cleanup acceptance

[Actual owned controls](docs/reverse-engineering/2026-10-12-native-failure-wait.md) reject normal root43 job exits despite drained receipts; root0 controls resolve.4actualchildwait42/raw10752,32exactpeerbytes,zeroabortrequests;19resealedfaults. Known children finish before roots; root-first failure remains distinct. Both milestones open.

### 2026-10-12: root-first kernel exit accounting

[Owned kernel-event adapter](docs/reverse-engineering/2026-10-12-root-first-exit.md) confirms roots43/0 exit before known setsid children42 during supervisor drain.4actualwatcherwait0,32exactpeerbytes;28resealedfaults. Exit events do not prove child reaping. Initial macro build failure/source retained, corrected. Both milestones open.

### 2026-10-12: child signal versus ordinary exit

[Owned kernel contrast](docs/reverse-engineering/2026-10-12-child-signal-exit.md) distinguishes defaultSIGTERM rawstatus15 from handlerexit42/raw10752.3verifiednativecontrols,16exactpeerbytes;20resealedfaults.1startupharnessfailure retained, fixed within original4slots. Default A/A, failedstartupcleanup and reaping remain unqualified. Both milestones open.

### 2026-10-12: stopped-child prediction falsified

[Independent stopped-state/exit gate](docs/reverse-engineering/2026-10-12-stopped-child-exit.md) confirms SSTOP4 twice, yet child kernel termination isSIGTERM15 in stopped and running contrasts.4nativecontrols,16exactmarkerbytes;22resealedfaults. OriginalSIGKILL9 prediction/assertion failure retained;3remaining slots passed revised expectation. Reaping and milestones remain open.


### 2026-10-14: SIGTERM-ignoring child exit contrast

Two owned controls independently report child SIGKILL9 after root wait43; default/stopped controls previously reported SIGTERM15. Six resealed faults reject corrupted disposition/status/receipt/identity/wait/prediction. Child reaping and both milestone acceptance contracts remain open. Evidence: `research/evidence/ignore-child-exit-2026-10-14`; manifest SHA-256 `165439fb1e3694fe80dd3c354644047aa4cd2abe55a537063de86bc347cab3ec`. Next: supervisor deadline contrast.


### 2026-10-14: Independent ignored-SIGTERM verifier hardening

Original native evidence remains sealed. Reader now independently rejects changed birth identity, ancestry/session topology, executable path, raw empty-output digests, broadened cleanup scope, malformed process state, root exit decode and watcher diagnostics. Fifteen resealed faults pass rejection checks; six isolated reader tests pass. No new native acquisition. Both milestones remain open.


### 2026-10-14: Supervisor deadline with ignoring child

Two actual owned controls independently report root SIGTERM15 and child SIGKILL9; supervisor target wait -15/failure deadline/drained true, client original deadline error retained without private abort/emergency closure. Fifteen resealed faults and six isolated reader tests pass. Child reaping and both milestone acceptance contracts remain open. Evidence `research/evidence/ignore-child-deadline-2026-10-14`; manifest `d7bf6100d00219454f30a3b7173b03e6556e31d9cb50b20c4e29d41cfcf81bae`. Next: private client abort contrast.


### 2026-10-14: Private abort with ignoring child

Two actual owned private cancellation controls independently report root SIGTERM15 and child SIGKILL9. Original client abort error retained; supervisor wait -15/failure abort/drained true with no emergency closure. Asynchronous owned watcher permits independent cancellation. Eighteen resealed faults and six isolated reader tests pass. No child reaping or universal callback claim. Evidence `research/evidence/ignore-child-abort-2026-10-14`, manifest `6cd44a4174726c56de64192ef2542dbe59a4d36d32875815f4edcdac28243ff8`. Both milestones remain open. Next: independent compiler descendant-wait gap.


### 2026-10-14: Actual Rustc direct-child waits

Pinned actual Rustc is directly observed with full birth/path/parent/session rechecks before two owned SIGTERM cancellations, actual waits -15; two positive metadata builds wait0. Every deterministic source byte and empty output stream digest is independently verified. Eight resealed faults and six isolated reader tests pass. This establishes direct-parent wait capability, not existing supervisor descendant wait or Native Canvas acceptance. Evidence `research/evidence/rustc-child-wait-2026-10-14`, manifest `0aa66cc68048448ca0bcdecf65b07bf1e3f4c318b0b90052efdcaca2d5ac1d46`. Both milestones remain open.


### 2026-10-14: Correlated actual Rustc kernel and parent waits

New signal-free single-process exit adapter independently registers full birth/path before cancellation. Two actual Rustc controls acknowledge registration before owned SIGTERM; parent waits -15 match kernel raw15, watcher waits0. Complete deterministic source bytes and empty outputs verified. Eleven resealed faults and six isolated tests pass. Existing supervisor descendant correlation and Native Canvas acceptance remain open. Evidence `research/evidence/rustc-kernel-wait-2026-10-14`, manifest `bce3ef86bcf8db11e78c597c16f34b01305a131dde6f2131c0d52a947d4db849`. Next: source builder supersession registration gate.


### 2026-10-14: Actual builder compiler kernel capture; recovery failure retained

Registration-gated source supersession independently captures actual Rustc raw kernel status15, watcher wait0 and CLI root abort wait-15/drained true. Baseline matches all32768 bytes including168padding/31872tail. Recovery generation3 hits supervisor deadline before generated-stage artifact; subsequent frame assertion fails with baseline retained. Three-build budget exhausted once, no retry/extension. Original producer failure/stage records sealed. Eight resealed faults and six isolated reader tests verify scoped partial measurements. Parent compiler wait and successful recovery remain unqualified. Evidence `research/evidence/builder-kernel-cancel-2026-10-14`, manifest `f531ba17e0232a64f1016dae2aab82c183122994e5b7f2fe055605ac625bc946`. Both milestones remain open. Next: independent recovery snapshot timing diagnosis.


### 2026-10-14: Independent toolchain snapshot timing

Two current full snapshots take0.857/0.750 seconds, six compiler query waits0,61 inventoried files/233810837bytes per snapshot, unchanged pinned canonical identity. Query bytes/digests and full inventory entries independently verified; no binaries copied. Eight resealed faults/six isolated tests pass. Persistent current snapshot slowdown is contradicted; historical recovery deadline cause and recovery acceptance remain unqualified. No builder rerun/timeout extension. Evidence `research/evidence/toolchain-snapshot-timing-2026-10-14`, manifest `666005d77ad22e8d22ccbc00453867cf7adfa31a4eb24550499914dfe93b90d9`. Next: owned CLI phase marker. Both milestones open.


### 2026-10-14: Owned CLI phase markers with retained deadline

Pinned unchanged CLI phase wrapper localizes first instrumented deadline after successful compiler wait and before final identity marker, with no receipt/frame admitted. That first seal/failure stays retained. Remaining slot starts tracing after imports, same baseline source: six markers, successful receipt/frame and closure. Full16384-byte frame including84padding/15936tail,17011 paired module bytes and1288 historical warning bytes verified. Eight resealed faults/six isolated tests pass. Shared budget2/2, no extension/reset. Historical recovery cause remains unknown; baseline success does not qualify recovery. Evidence `cli-phase-build-2026-10-14` and `cli-phase-optimized-2026-10-14`. Both milestones open. Next: optimized phase wrapper for changed recovery diagnostic.


### 2026-10-14: Zero CLI wait and valid receipt under deadline verdict

Optimized phase recovery diagnostic stops after baseline prerequisite fails: six markers,821-byte valid receipt,17011-byte known baseline WASM and actual CLI wait0 coexist with drained supervisor deadline verdict. Client rejects and publishes no frame; final closure zero workers/timers/revision0. Eight resealed faults/six isolated tests validate scoped boundary. One of three slots used; no supersession/recovery or unchanged retry. Completion-before-deadline remains unknown without absolute supervisor/exit timing. Evidence `research/evidence/builder-phase-recovery-2026-10-14`, manifest `c27420b678797874359771e51d550a2e25bfcca645fc25f380bdc087df2d50b4`. Both milestones open. Next: absolute timing adapter.


### 2026-10-14: Same-clock deadline and target poll audit

Pinned unchanged anchor body is instrumented with passthrough real monotonic calls and actual target polls. Case0 deadline decision+32ms and first terminal wait-15+117ms retained; case1 wait0 observed41ms before its deadline admits full16384-byte baseline frame including84padding/15936tail. Both closures zero workers. No false deadline observed; historical zero-wait/deadline timing remains unknown. Eight resealed faults/six isolated tests pass. Two slots consumed once, no extended deadline. Evidence `research/evidence/deadline-poll-audit-2026-10-14`, manifest `ded812fbefea48a7ad2272f18b255aeb5c709f1379557d2011d439c8ae9b8d40`. Both milestones open. Next: labeled post-completion observer-delay control.


### 2026-10-14: Injected post-completion scheduling delay

Two owned peer controls share0.2s delayed public observer. Both actual target waits0 are observed before1s deadline. Baseline resolves; explicit post-completion sleep crosses deadline and reclassifies completed peer as deadline, with drained receipt/no emergency closure. Real clocks/poll results pass through, no fabricated time/status. All16 sender payload bytes and receiver digests/text verified; eight resealed faults/six isolated tests pass. No compiler builds/pixel claims/deadline extension. Production policy unchanged and historical compiler cause unknown. Evidence `research/evidence/post-completion-delay-2026-10-14`, manifest `4be710fd1073a391fda6312839abad9fddcf7a96531710f86aac20aeecd9ed15`. Both milestones open. Next: observed-completion guard evaluation.


### 2026-10-14: Preserve observed completion before deadline

The supervisor previously reclassified an actual terminal target poll observed before the deadline when subsequent scheduling delay crossed that deadline. The production guard remembers only terminal completion observed by the supervisor's own monotonic clock before the deadline. Private abort is checked first. First terminal observation after the deadline remains a deadline failure; cleanup deadlines are unchanged.

Four corrected owned native peers exercise delayed success (wait 0), delayed original failure (wait 43), genuine late completion (wait 0 first observed after deadline), and abort precedence (wait 0 with abort verdict). Explicit post-completion sleeps cross the deadline in the first two controls. Real poll results and clocks pass through unchanged. All 32 sender bytes, admitted receiver bytes/digests and UTF-8 replacement text match independent expectations. No pixel allocation or padding claim is made by these peer-only controls.

The initial four-slot campaign used invalid os.alarm, producing three failed assertions; its fourth abort assertion passed but cannot qualify the intended fixture. All original failures are sealed in research/evidence/completion-guard-2026-10-14. The corrected signal.alarm campaign used four separately declared slots; total eight owned peer jobs and zero compiler builds. Neither campaign's budget was reset.

Corrected evidence: research/evidence/completion-guard-corrected-2026-10-14, manifest SHA256 1d51e5d0157a2159b9b9fdc35d707046173ac00751e4c738dbde82d10bdf5299. Eight resealed fault mutations and six isolated tests verify acceptance separately from acquisition. Current REA ARM64 public helper identity is recorded in provenance-note.json; rea-status.json explicitly retains prior preflight provenance. Private Xcode capture bridge remains unavailable. No owned Xcode workspace was opened.

Historical compiler timing causes remain unknown. This change establishes scoped production supervisor completion semantics, not physical resource reclamation, unseen process coverage or native Canvas protocol evidence. Both milestones and issues 15, 19, 22 and 25 remain open. Next: a bounded compiler recovery experiment using this guard, or independent native interaction evidence when its prerequisites change.


### 2026-10-14: Actual compiler recovery with completion guard

Three actual owned Rust CLI builds exercise baseline, cooperative supersession and recovery with the verified production completion guard. Baseline and generation3 publish independently expected allocations; generation2 preserves the original abort and drained CLI wait -15. A full-birth identity public kernel watcher registers before cancellation and independently reports the observed Rust compiler NOTE_EXITSTATUS raw15 (SIGTERM). Its actual watcher wait is0. The compiler's parent wait is not observed and physical reclamation remains unqualified.

All49152 retained bytes match independent pinned expectations, including252 row-padding bytes and47808 unused allocation-tail bytes. Both accepted source receipts, generated sources and WASM hashes match retained files; both wrappers complete six original CLI phase markers within the unchanged five-second job deadline. All three jobs are fresh, with one three-stage budget, no reset and no retries. Closed source loop reports zero live workers/timers and revision2.

Evidence: research/evidence/guard-compiler-recovery-2026-10-14; manifest SHA256 cd51dc98fcd0383e1b50a6efbd3577b3b28557796087e867944d47897c8a3a2e. Twenty resealed verifier mutations and six isolated tests separate delivery acceptance from acquisition. Current REA ARM64 Rustc identity is retained separately from carried prior preflight/environment records. Actual compiler/public observer file hashes were verified immediately before acquisition. No Xcode workspace was opened; private capture bridge remains unavailable.

This changed-condition run establishes finite owned source builder cancellation and recovery with independent compiler kernel termination evidence. It does not prove the cause of historical deadlines, compiler parent wait, arbitrary process quiescence, kernel allocation reclamation or native Canvas protocol behavior. Historical failures remain sealed. Milestones and issues15/19/22/25 remain open. Next: independent R1/R2 or native interaction evidence when its prerequisites are available; do not repeat unchanged successful compiler controls or missing bridge attempts.


### 2026-10-14: Native failed-send restored rights

Two owned single-task controls fill a private receive queue to its declared limit1, then attempt an IOSurface attachment send with zero timeout. Both COPY_SEND and MOVE_SEND report MACH_SEND_TIMED_OUT (268435460); the queue retains only the original filler. After draining it, immediate receive reports MACH_RCV_TIMED_OUT (268451843), so the failed attachment was not queued.

Native returned descriptor disposition is MOVE_SEND (17) for both inputs. Failed COPY_SEND preserves the original name and raises its send urefs from1 to2. Failed MOVE_SEND removes the original task-local name and returns a different name with1 send uref. Destination COPY_SEND also restores an extra endpoint uref (2 total). The follow-up probe measures original and returned names independently, removes every measured restored resource/send endpoint reference, then removes the private receive right. Retained CF alias bytes remain readable after local right release; this does not establish kernel reclamation.

All98304 bytes in six returned-name captures match independent 17x9/stride128/seed49 expectations, including3240 padding bytes and91392 unused allocation-tail bytes. An additional98304 bytes in the prior partial native controls match the same independent expectations. The initial partial MOVE control did not measure/remove its returned name; its explicit resource cleanup is unqualified, and its bounded owned process exit is retained separately.

Initial compilation failed for a missing libbsm link; the compiler failure is retained. Two sandboxed surface-creation failures are retained in research/evidence/surface-send-timeout-2026-10-14. Authorized native access enabled two partial controls in research/evidence/surface-send-timeout-native-2026-10-14; two changed returned-name controls follow in research/evidence/surface-send-returned-2026-10-14. Six owned task executions total, two slots per declared campaign, no reset and no existing app interaction. Native acquisition used alarms5s/outer7s and the exclusive controller lock. Compilation was bounded30s.

Returned-name manifest SHA256: 385cb1f21b9fbef2c4f11b827349f0144b2fc9baba7b3981dc4d78122d71404d. Eight resealed faults and six isolated tests separate verification from acquisition. REA6.2.0 verified the current owned ARM64 probe binary SHA256 db0f71dcdc7ac54b2cbc2cf38276aa9dba4fb1283db55f3c96c805d80b767018; no binaries are published. Private Xcode bridge remains unavailable and no workspace was opened.

This is owned public Mach/IOSurface failure accounting, not live Canvas transport, physical release, peer authentication or cross-platform delivery evidence. Both milestones and issues15/19/22/25 remain open. Next: compare explicit mach_msg_destroy of returned failed envelopes while tracking original/returned rights separately; do not repeat completed controls unchanged.


### 2026-10-14: Destroy returned failed envelopes once

Two newly owned native task controls extend the full-queue timeout experiment with exactly one mach_msg_destroy of the returned failed attachment envelope. Before destruction COPY_SEND has original/returned resource urefs2 at one name; MOVE_SEND has original urefs0 and returned urefs1 at a different name. The destination endpoint has2 urefs in both cases.

After destruction COPY_SEND retains exactly its original1 resource uref, MOVE_SEND returned urefs fall to0, and both destination endpoints retain1 original uref. The probe then explicitly removes remaining original resource and endpoint rights and the private receive right. Original and returned names are checked separately after cleanup. The original queue filler remains the sole queued message and an immediate receive after draining it times out. Legacy output field resource_refs_after_failure denotes the post-destruction measurement in this derived probe; the first JSONL row records the separate before-destruction values.

All98304 bytes across six allocation captures match independently constructed17x9/stride128/seed49 expectations, including3240 padding bytes and91392 unused tail bytes. Retained CF aliases remain readable after right cleanup. This measures public Mach right accounting and retained alias usability, not physical reclamation or native Canvas transport.

Evidence research/evidence/surface-send-destroy-2026-10-14; manifest SHA256 bc202e0c981843dd6af7f4c536c5bfc54e1c77c4290526839e9753fdb3699c4c. Two declared slots, two executions, alarms5s/outer7s, bounded30s compilation and exclusive controller lock. No existing app/process interaction or Xcode workspace. Ten resealed faults and six isolated tests separate verification from acquisition. REA6.2.0 independently identified owned ARM64 probe SHA256 07b235981af5ce1d1cb79e5640f842fe19e62ea153f49021cec1c1b5a0653614. No binaries published.

Earlier compile/sandbox failures and partial returned-name cleanup measurements remain sealed. Both milestones and issues15/19/22/25 remain open. Next: independent resource/generation reuse or receiver/completion ordering; no unchanged repetition of this qualified boundary. Private Xcode bridge remains unavailable and is separate from live REA.


### 2026-10-14: Native returned-envelope retry

Two newly owned native task controls fill a private Mach receive queue, time out an IOSurface descriptor send, drain the filler, and retry the actual returned envelope without reconstructing its header or descriptor names. Both retries succeed. The returned header remote type and descriptor disposition are MOVE_SEND (17), despite the initial destination using COPY_SEND.

For the COPY_SEND attachment, the original, returned and received names coincide. Resource send urefs progress 2 → 1 after retry send → 2 after receive → 1 after received-envelope destruction. The original send reference survives. For MOVE_SEND, original, returned and received names differ; returned urefs progress 1 → 0 after retry send, the received name has one uref, and received-envelope destruction removes it. Destination urefs fall from two to one on retry. Final explicit cleanup removes all remaining measured send references and the private receive right.

All 131,072 bytes in eight allocation captures match independently constructed 17×9, stride 128, pattern-seed 49 expectations, including 4,320 row-padding bytes and 121,856 unused tail bytes. Imported CF aliases remain usable after right cleanup and release of the original CF aliases. Both sequential task controls happen to report numeric surface ID 122; this does not establish cross-task allocation identity or encode frame generation. No physical reclamation or native Canvas protocol claim follows.

Evidence: research/evidence/surface-send-retry-2026-10-14. Manifest SHA256 dd67a2fa3a3f083e487f8bec30dafe634551bc4268ffb3d11e416e67151c47d6. Two declared slots, two executions, alarms of five seconds, outer deadlines of seven seconds and compilation bounded to thirty seconds. All acquisition uses the exclusive controller lock and authorized native access. Six isolated tests and twelve resealed faults verify acceptance separately from acquisition. REA 6.2.0 identifies the owned ARM64 probe SHA256 408de41cbb83abb164127905a736fa78768763f82a79f76d257ff5ba3e3060f7. No binaries are published.

Earlier failure, restoration and destruction evidence remains sealed. The private Xcode capture bridge is unavailable; no Xcode workspace was opened. Both milestones and issues 15, 19, 22 and 25 remain open. Next: independent lifecycle/transport or resource-generation evidence, without repeating this qualified retry boundary unchanged. Reconcile the prior ambiguous GitHub comment before resuming external issue updates.


### 2026-10-14: Native invalid-destination ownership

Two newly owned native task controls remove an endpoint's receive right before sending an IOSurface attachment, leaving one destination dead-name reference. Both sends report MACH_SEND_INVALID_DEST (268435459). Original and returned resource names coincide, resource send urefs remain one, and the header remote type remains COPY_SEND (19). The attachment disposition remains the requested COPY_SEND (19) or MOVE_SEND (17).

One mach_msg_destroy preserves the COPY_SEND attachment's original reference but consumes the MOVE_SEND attachment's reference. The destination dead-name reference stays one in both controls; the probe explicitly removes it and any remaining original resource send reference afterward. Retained CF aliases remain readable after cleanup. This differs from the pinned full-queue timeout controls, where COPY_SEND acquires a returned extra reference and MOVE_SEND returns another name. A single blanket assumption that every send error has normalized returned ownership is falsified. Rejection before descriptor copy-in is an interpretation consistent with these observations, not a traced kernel execution order.

All 98,304 bytes in six captures match independent 17×9, stride 128, pattern-seed 49 expectations, including 3,240 padding bytes and 91,392 unused tail bytes. Two declared slots, two executions, five-second alarms, seven-second outer deadlines, compilation bounded to thirty seconds and exclusive controller locking. No retries, existing app/process interaction or Xcode workspace. Six isolated tests and twelve resealed faults separate verification from acquisition.

Evidence: research/evidence/surface-invalid-destroy-2026-10-14. Manifest SHA256 a18ecb92916246ca58361d2df158cf9bd12fcb24d6621da910765e4d5fb9ef11. REA 6.2.0 identifies the owned ARM64 probe SHA256 07dda5f443ba9f812a26db99e8b1ea7843f6c7cc2ed740bea4637a360a456e6e. No binaries are published. Prior timeout, restoration, destruction and retry results remain sealed.

This qualifies two public owned send-error ownership cases, not every Mach error, physical allocation reclamation or native Canvas protocol behavior. Private Xcode capture bridge remains unavailable. Both milestones and issues 15, 19, 22 and 25 stay open. Next: discriminate another unmeasured ownership/error boundary or independent native interaction gate; do not repeat this completed boundary unchanged.


### 2026-10-14: Later descriptor failure and original send rights

Two owned native controls send a valid IOSurface descriptor followed by a receive-only name incorrectly requested as MOVE_SEND. Both sends report MACH_SEND_INVALID_RIGHT (268435466). The destination queue stays empty. The receive-only name retains its receive right before and after destruction of the failed envelope.

With the first descriptor COPY_SEND, its original/returned name is unchanged and one send reference remains before and after failed-envelope destruction. With MOVE_SEND, the same numeric name remains in the failed envelope but queries already report zero send references before destruction, and still zero afterward. No usable original send reference is restored. The destination retains one send reference; header remote type remains COPY_SEND (19), and descriptor dispositions remain the request types. This differs from both invalid-destination and full-queue timeout outcomes. Internal kernel copy-in/rollback ordering was not traced and is not claimed.

The first two controls measured this transition but did not query final send-reference removal. A changed two-slot follow-up adds explicit zero-send-reference checks after cleanup; both pass. All 98,304 follow-up bytes match independent 17×9, stride 128, pattern-seed 49 expectations, including 3,240 padding bytes and 91,392 unused tail bytes. Another 98,304 bytes in the first controls match the same independent expectations. CF alias bytes remain readable after cleanup; physical allocation reclamation is unqualified.

Four owned executions total, two slots per declared campaign, no reset or retry. Five-second alarms, seven-second outer deadlines, thirty-second compilation bound and exclusive controller lock. The first source, outputs and binary identity are retained in research/evidence/surface-partial-right-2026-10-14; the explicit cleanup follow-up is research/evidence/surface-partial-cleanup-2026-10-14, manifest SHA256 d8c5acef6c6154e836c639869591d0e18d226576cc7bcbf9b9cf6ce6488f1d76. REA 6.2.0 identifies follow-up ARM64 probe SHA256 30302e9fae7108856afb51a29b821ebd057db0e291967605aea72a7e10adf5c4. No binaries are published.

Six isolated tests and twelve resealed faults separate verifier acceptance from acquisition. No existing app/process interaction or Xcode workspace. Private Xcode bridge remains unavailable. This is scoped public owned Mach failure accounting, not native Canvas transport or a general Mach error policy. Both milestones and issues 15, 19, 22 and 25 stay open. Next: independent unmeasured lifecycle/transport evidence; do not generalize envelope disposition or unchanged numeric names into ownership after arbitrary errors.


### 2026-10-14: Bounded source short reads

The production file loop previously treated one readSync return as the entire source. An owned wrapper caps each real file read to seven bytes without fabricating the returned bytes. Before the fix, a valid 202-byte source reaches the builder as a seven-byte prefix and fails; an oversized ASCII file also incorrectly reaches the builder as that prefix. Empty input is correctly rejected.

The loop now reads into its fixed 4,097-byte buffer until EOF or the sentinel limit, advancing both destination offset and file position by the actual bytes read. The same six before/after file cases retain all real read results. The valid file takes thirty calls including EOF, reaches the builder with its exact complete digest and publishes the independently expected 16,384-byte allocation. Oversized input stops after 586 capped reads at the sentinel and never reaches the builder; empty input stays rejected. File descriptors close once in every case, and workers/timers are zero after closure.

All 16,384 published bytes match the independent finite-source oracle and pinned owned fixture, including 84 row-padding bytes and 15,936 unused tail bytes. The adapter uses a prebuilt owned WASM fixture and actual V8 execution, with no fresh compiler build. This is an injected short-read boundary using real file bytes, not evidence that ordinary local reads naturally returned short. It does not establish atomicity against concurrent in-place writes, arbitrary filesystem latency, Windows execution or native Canvas state/transport semantics.

Evidence: research/evidence/source-short-read-2026-10-14; manifest SHA256 56003fc77eaeadfbd631fb31485239e79fc8409563bd1eee03d4590e236ed900. Two declared before/after slots, each bounded to eight seconds, under the exclusive controller lock. REA 6.2.0 independently identifies Node ARM64 binary SHA256 768d7cb3d8a404059b095085b2a3803bcb1c8965e0b8eb95fc453bad9196974e. Six isolated tests include actual file reload/closure and nonregular/path-replacement regressions; twelve resealed faults reject false byte/read/lifecycle claims. Both source versions and the original rejected-prefix measurements remain sealed.

No Xcode workspace was opened; the private capture bridge remains unavailable independently of REA. Both milestones and issues 15, 19, 22 and 25 remain open. Next: independent remaining source/state/interaction boundary; retain the bounded input and no-follow descriptor checks.


### 2026-10-14: Safe primitive observer failures

The observer client previously stored arbitrary thrown callback values directly. Truthy primitives caused a TypeError when its close handler attached the cleanup record, leaving the job promise unsettled. Falsy values were overwritten by the later supervisor abort error. Plain opaque objects could escape as non-Error rejections; frozen Errors and Errors with read-only record properties also broke final record attachment.

Cancellation now converts non-Error reasons into Error objects before selecting the first failure. Ordinary same-realm Error objects retain identity. If a reason cannot be converted to a string, a stable non-Error failure message is used. Cleanup record attachment uses a data property; immutable or incompatible Error objects are copied with the original message into a writable Error that carries the record. This preserves failure delivery without changing private abort, native drain or output-byte accounting.

Twenty-four before/after source controls cover strings, zero, false, null, undefined, empty string, bigint, symbol, opaque object, ordinary Error, frozen Error and read-only record. The initial unsettled/overwritten outcomes remain sealed. Two newly owned native controls throw string and false after identifying an acknowledged setsid child. Both return the normalized original message, one private abort request, a drained receipt, root wait 43 and actual parent-recorded child wait 42 (raw status 10752), with zero remaining observed descendants and no emergency closure. All sixteen child payload bytes match independent expectations. This is sampled owned process cleanup, not universal process quiescence, physical resource release or Canvas transport.

Evidence: research/evidence/primitive-callback-2026-10-14; manifest SHA256 cc30d90cbf294b92d37b9ab76e5d31b4bb899d038eeb2f71ace5a4e0e044d71f. Two source phase slots and two native slots, no reset. Each source/native parent has an eight-second outer bound, native targets have six-second alarms, and acquisition uses the exclusive controller lock. REA 6.2.0 verifies the ARM64 public observer SHA256 718c0dd47aaa6598281d0f0afb7dd12fa4c497a8494897b24829905de82ecda5. No binaries are published.

Six isolated tests include twelve resealed faults, frozen historical raw-output checks and twenty-four fresh current-client raw stream controls. Historical source remains hash-pinned rather than incorrectly required to equal the latest client. No async/Promise-returning callback support is qualified. No Xcode workspace was opened; private bridge remains unavailable. Both milestones and issues 15, 19, 22 and 25 stay open. Next: an independently scoped remaining lifecycle/callback or native interaction boundary.


### 2026-10-14: Synchronous observation callback contract

Observation callbacks returning promises or thenables previously escaped the synchronous cancellation path. Twelve frozen source controls retain before/after results: resolved, rejected, pending and custom thenable results now reject with an explicit synchronous-contract error; throwing then getters retain their original error, and plain synchronous return values remain accepted. The rejected promise is consumed to prevent unhandled rejection. Before behavior is captured with a controlled source-only unhandled-rejection listener; unsafe before native jobs were not launched.

Two owned native controls return resolved and rejected promises after observing a root and its ready detached child. Both request private abort, retain root completion 43 and actual child wait 42, report drained with zero remaining observed processes, and preserve all 16 controlled payload bytes against independent expectations. No emergency cleanup was required. Source and native acquisition budgets each remain two of two consumed.

The independent sealed reader checks source hashes, full raw payloads, receipts, identities, cancellation and outcomes. Twelve resealed faults must fail verification. Current primitive-error handling receives twelve fresh source regressions; raw output accounting receives 24 fresh controls. Historical native evidence stays frozen.

This rejects unsupported asynchronous callback results; it does not await callbacks or add asynchronous callback support. Job deadlines and owned drain semantics are unchanged. Evidence qualifies the owned observer adapter, not native Canvas protocol, physical IOSurface reclamation, arbitrary noncooperative JavaScript or unseen processes. The private Xcode bridge remains absent; REA availability is separate. Both milestones and issues #15, #19, #22 and #25 remain open.

Evidence: `research/evidence/thenable-callback-2026-10-14`; manifest SHA-256 `d7ea916d9d6d23b371cf5425f0b76665b09fb70c6aeb6a555368442f4b31ac3b`. Next work: choose an independent eligible native or portable experiment; do not repeat these completed callback controls.
