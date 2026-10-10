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
