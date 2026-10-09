# Remaining work and acceptance plan

Planning baseline: 2026-10-09, verified implementation checkpoint `3e91d33`. This replaces the original roadmap's assumed sequence and dates with evidence-based dependencies. The original `plan.md` remains a proposal, including its illustrative protocol and toolchain assumptions.

## Outcome and current state

Target: a documented, bounded preview product that compiles an explicitly supported Swift view subset, produces a portable image, and supplies a reproducible compatibility report against pinned native references. Unsupported constructs must fail clearly. Broader SwiftUI compatibility is a later expansion, measured feature by feature.

The repository currently contains the RE toolkit, not the Rust preview product. It has 25 reviewed adapters, 19 research MCP tools, 140 passing tests, scoped claims, immutable local evidence and published synthetic goldens. Verified boundaries include plist serialization/decoding, local raw-XPC coding, static message strings, and owned CPU IOSurface Mach handoff with clean/abrupt sender and receiver exits. Receiver-first controls also measure local send-right counts and retained-port access after original CF release. Paired live-peer timeout controls distinguish open/revoked reply endpoints with graceful cleanup and full padded-byte checks. Independent V8 and WasmKit rectangle checks now pass on macOS, including injected faults and whole-buffer invalid-request controls; source-to-IR and non-Apple execution remain open. Static default diagnostics, cancellation action guards and destructor diagnostic skips and stored cancellation callback/isolation and invalidation weak-owner/state boundaries now have finite mutation-tested checks; instruction-body acceptance rejects headings and groups aliases. Owned shared-BGRA GPU completion and retained CF access after explicit Metal reference drop now pass full-allocation comparisons on Apple M1; Completed GPU-to-CPU audited Mach handoff and clean/abrupt receiver exit now pass full-allocation/local-right checks; receiving-process Metal readback also passes independent destination-byte checks; actual Canvas and unsynchronized GPU ordering/failure handling remain open. These do not establish the full Xcode protocol or portable SwiftUI execution.

Blocking gaps: Xcode tool responsiveness is restored using one retained approved broker, and explicit solid red/blue controls render exact center patches, and pinned light-scheme inline/custom text fixtures now repeat exactly with visible label change; mapping-verified native instrumentation attach cancels before session creation. The [pinned light fixture](reverse-engineering/2026-10-09-light-root.md) establishes full-window native repeat and controlled interior change. The [same-definition dark/light/dark reversal](reverse-engineering/2026-10-09-scheme-switch.md) removes the earlier title confound and restores original PNG/pixels exactly; independent whole-frame predictions, full environment coverage and correlated request/reply trace remain open. ImageRenderer remains a separate native reference path.

Two gates control the project:

- **Native oracle gate:** reliably capture the behavior we intend to reproduce, with repeatability and positive-change controls.
- **Portable execution gate:** demonstrate a small, explicit source subset through the intended portable compiler/runtime boundary. Native Apple SDK builds do not establish this.

If the canvas gate remains blocked, portable-subset research can use a separately labeled ImageRenderer oracle. It must not claim Xcode wire compatibility. If portable compilation fails, investigate a smaller compatibility source layer or intermediate representation; do not assume a compiler flag or xtool fork solves missing runtime/framework semantics.

## GitHub delivery milestones

1. **[0 → Reverse-engineered](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/1).** Finish native oracle, relevant protocol and resource semantics, native decoder/replay, and a versioned coverage/unknowns report. Toolkit completion alone does not close this milestone. Pin the native baseline and explicitly cover each claimed platform/output path; unresolved required semantics keep it open.
2. **[Reverse-engineered → Fully cross-platform WASM canvas](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/2).** Reimplement the recovered supported contract using portable compilation/compatibility source, WASM execution, Rust core, layout/rendering, developer canvas and hot reload. The product execution path must not depend on Apple frameworks, Mach, Xcode or a simulator. Native Apple tools remain reference oracles. Linux, macOS, Windows and browser execution claims require actual target checks; full feature coverage must be measured against the declared recovered contract, with no silent native fallback.

The [verified toolkit baseline](https://github.com/aspauldingcode/xcpreviewer-rs/issues/1) is completed; the remaining tasks are linked below. Milestone progress counts issues, not proof of universal behavioral coverage.

R1 partial checkpoints: [receiver-first experiment](reverse-engineering/2026-10-09-surface-receiver.md) and [selected failure/timeout cleanup controls](reverse-engineering/2026-10-09-surface-failure.md) pass. [Global ID lifetime controls](reverse-engineering/2026-10-09-surface-id-lifetime.md) falsify universal immediate ID disappearance; a separately requested 100ms followup is null in all executions, without proving delay causality or memory reclamation. Final reclamation and broader required failure coverage still keep R1 open. R2 now has measured use-state and [owned delayed-reuse countermodel](reverse-engineering/2026-10-09-reuse-renderer.md) boundaries; [Immediate imported-name lookup boundaries](reverse-engineering/2026-10-09-retired-name.md) now distinguish remaining Mach rights from retained CF aliases; [Native static IOSurfacePayload keys](reverse-engineering/2026-10-09-payload-keys.md) now corroborate five codec fields without a named generation/completion field inside that type; [Surrounding codec boundaries](reverse-engineering/2026-10-09-codec-boundaries.md) distinguish stored fields from returned keys and recover the singleton identifier alias; [static archive/unarchive sites](reverse-engineering/2026-10-09-service-identifier.md) select optional Swift.String under that inner key; [Static transport callbacks](reverse-engineering/2026-10-09-transport-reply.md) distinguish success/error payload routing and encoding fallbacks; [Owned wrapper data controls](reverse-engineering/2026-10-09-plist-data-decode.md) measure empty-data/non-dictionary fallback without forcing the live serialization failure; [Static continuation guard](reverse-engineering/2026-10-09-continuation-guard.md) locates locked first-fulfillment state and callback suppression; native race/cancellation controls and actual Canvas generation/completion ordering remain open. O3 now has ImageRenderer A/A repeat and controlled A/B pixels in its separate reference tier; live Canvas capture remains unverified.

O2 now has a [sealed direct-route diagnostic](reverse-engineering/2026-10-09-xcode-bridge.md): bypassing discovery and supporting reverse requests did not produce a tool response. Subsequent [retained-access controls](reverse-engineering/2026-10-09-xcode-access.md) restore tool responses after explicit approval and reuse that connection across workers. Corrected native content checks reject blank snapshots; the [solid-view controls](reverse-engineering/2026-10-09-solid-controls.md) now establish a narrow non-text content path, while text/layout and complete frame acceptance remain open.

The [first no-import WASM rectangle control](reverse-engineering/2026-10-09-portable-solid.md) matches complete native solid RGBA, but uses hand-authored C and establishes no Swift frontend or text/layout support. Feasibility experiments in milestone two can run before milestone one closes. Release acceptance still depends on native references and the final feature/coverage contract. Milestone two's aim is a cheaper, hot-reloadable canvas for Apple app development; that performance claim needs measured native-versus-portable workloads.

## Ordered backlog

| ID | Work | Prerequisites | Required output and acceptance |
| --- | --- | --- | --- |
| [O1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/2) | Reconcile target/environment identities and invalid evidence | Existing toolkit | Verify current target hashes/UUIDs, classify invalid/changed runs, retain historical results; no stale success reused after drift |
| [O2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/3) | Native capture diagnosis | [O1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/2) | Separate bridge initialization/schema failure, preview launch, attach, hook readiness and rendering; each diagnostic answers one question |
| [O3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/4) | Stable reference fixtures | O2 for canvas; existing ImageRenderer for its own tier | A/A unchanged capture and controlled A/B change; geometry, scale, fonts, appearance and color profile pinned; accepted pixels and capture scope recorded |
| [R1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/5) | Receiver-first exit and release accounting | Existing Mach surface handoff | Sender remains valid after peer exit; owned rights/references accounted for on success, failure and timeout; no final-release reclamation claim without a discriminating check |
| [R2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/6) | Resource reuse and completion model | [R1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/5) | Distinguish resource identity from frame generation; test stale handles, repeated frames, delayed consumers, acknowledgements, concurrent release and sequence gaps |
| [R3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/7) | Format and synchronization coverage | R2 and selected native output path | Measured stride/planes/format/orientation/color metadata; GPU producer-to-reader completion verified when GPU output is in scope |
| [P1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/8) | Recover one actual preview lifecycle | O3 plus working observation method | Launch-to-first-output capture with image identities, correlated request/reply, raw envelope, resource association and explicit coverage gaps |
| [P2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/9) | Recover bounded wire semantics | [P1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/8) | Measured fields, optionality, types, discriminants, version/capability negotiation, replies/errors, cancellation and ordering for the selected flow |
| [P3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/10) | Native decoder/replay adapter | P2 plus applicable R2/R3 | Decode frozen native fixtures, reject malformed/unsupported input, replay one selected result through an owned adapter; no invented fields |
| [F1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/11) | Choose first portable subset | O3 reference tier | Written feature contract and holdouts; proposed start: fixed composition, static text, simple colors and geometry, explicitly bounded state/assets |
| [F2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/12) | Compiler/runtime feasibility spike | [F1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/11) | One tiny source fixture traverses the chosen portable boundary and executes on an intended non-Apple host; record imported functions, framework/runtime dependencies and unresolved symbols |
| [F3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/13) | Design portable protocol and ABI | F2; P2 only for measured native mappings | Versioned schemas and capability/error semantics; explicit ownership, cancellation, frame/resource IDs and limits; native and portable envelopes remain separately identified |
| [I1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/14) | Rust workspace and core contracts | [F3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/13) | Typed request/result model, bounded validation, structured errors, lifecycle state machine, reproducible build and fixture tests |
| [I2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/15) | Swift compatibility/build adapter | F2 + I1 | Supported source builds deterministically with actual pinned tools; unsupported APIs diagnosed; build caches keyed by source/toolchain/options/target |
| [I3](https://github.com/aspauldingcode/xcpreviewer-rs/issues/16) | Runtime and host imports | I1 + I2 | Bounded instantiation, memory/fuel/time limits, host functions, traps/cancellation and deterministic fixture execution; runtime choice justified by F2 evidence |
| [I4](https://github.com/aspauldingcode/xcpreviewer-rs/issues/17) | Layout and software rendering | F1 + O3 + I3 | Implement only selected text/layout/shape/image features; documented fonts, metrics, alpha/color semantics, stride and PNG/pixel output |
| [I5](https://github.com/aspauldingcode/xcpreviewer-rs/issues/18) | End-to-end portable CLI slice | I2–I4 | Source to portable execution to image, on a non-Apple target, with explicit feature report and a measured native comparison |
| [H1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/19) | Transactional hot reload | I5; identity/cancellation contracts in F3 | Watch/debounce changes, incremental rebuild, replace WASM instance, preserve compatible state or declare reset, reject stale generations and keep last valid frame on build/runtime errors |
| [H2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/20) | Developer canvas | I5 + H1 + V1 | Open an Apple app fixture/project, select supported preview, inspect diagnostics, update canvas on edit and report unsupported features without native fallback |
| [B1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/21) | Cost and latency qualification | H1/H2 + stable native workload | Measure cold first-frame and edit-to-frame p50/p95, CPU, peak memory, cache-hit behavior and sustained reloads against equivalent native fixtures; publish hardware/settings/sample counts |
| [V1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/22) | Independent conformance system | O3; evolves alongside F1–I5 | Frozen native references, independent decoder/comparator, holdouts, injected faults, failure shrinking and machine-readable coverage reports |
| [A1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/23) | Preview-facing MCP and user workflow | I5 + H1 + V1 | Build/render/status/cancel/capability tools, bounded artifacts and clear unsupported-feature errors; research MCP remains separately identified |
| [A2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/24) | C ABI and language bindings | Stable I1/I5 API and actual consumer need | Stable handle/buffer/error ownership; C ABI first, then one demanded binding; equivalent results and cleanup under each wrapper |
| [S1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/25) | Hardening and platform acceptance | I5 + V1 | Unsupported inputs, resource exhaustion, crashes, timeout recovery, isolation and supported-platform CI verified |
| [D1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/26) | Packaging, releases and operator docs | S1 + selected A1/A2 | Reproducible installation, dependency/license inventory, release provenance, runnable examples and truthful compatibility matrix |

O/R/P/F work can inform each other without implying that every RE edge case blocks the first portable image. Actual wire replay needs P1–P3 and the relevant resource semantics. The portable CLI can use a declared independent contract after F2 succeeds. Multi-plane/GPU coverage and broad bindings are not prerequisites for a CPU-only static subset.

## Immediate experiment sequence

1. **Receiver-first exit.** Reverse the current ownership direction. Compare normal cleanup with abrupt receiver exit; check sender bytes, subsequent mutation, peer-death detection and rendezvous/child cleanup. Preserve exit status and every owned-right operation result.
2. **Release accounting.** Measure owned send/receive/dead-name rights at explicit checkpoints, with repeat loops and cancellation/error paths. Separate port-name counts, reference counts and surface references. Do not infer kernel surface reclamation from a missing user-space handle.
3. **Reuse and stale completion.** Send two deterministic frames sharing a surface and two using distinct surfaces. Delay acknowledgements deliberately. Verify frame-generation identity, required completion ordering and rejection of stale outputs. This remains a synthetic transport control until native behavior corroborates it.
4. **Discriminating canvas diagnosis.** Use the existing owned project and pinned build. Test one changed precondition or one smaller observation per attempt. Retain native diagnostics; distinguish content rendered by the app from the actual preview. Protected-process restrictions are not a reason to change system protections or re-sign Apple applications.
5. **Reference stability.** Freeze an ImageRenderer A/A/A/B corpus while canvas diagnosis continues. Label its oracle separately. Include text, padding, alpha, scale and Unicode positive changes; do not accept blank images or cached outputs as successful renders.
6. **Portable feasibility.** Run the smallest source subset through available candidate toolchains. Prefer existing working compiler/runtime paths. Install or fork additional tools only when an observed missing capability justifies them. Confirm execution on the intended portable host before expanding features.

Each experiment needs fixed expectations, a counterexample or positive control, timeout/artifact limits, ownership checks and a defined next action. A failed capture is not a renderer mismatch; a cleanup failure is not a passing lifecycle case. Avoid rerunning the entire campaign after every new adapter.

## Protocol recovery details

For the selected native flow, recover request IDs, version/capability fields, message selection, payload types, reply correlation, optional/missing fields, errors, cancellation, deadlines, reconnect/restart and output association. Verify the ten statically recovered strings in observed messages. Internal enum selectors must not become assumed numeric wire IDs.

Retain plist edge cases already measured: signed zero, bool/int distinction, integer boundaries, Unicode/NUL, malformed-data fallback and fixed raw-data slot behavior. Expand only where observed consumers require more cases. If encoder byte compatibility is required, implement and compare that boundary separately; Python semantic round trips do not supply Apple encoder parity.

For attachments, document sender/receiver ownership, right disposition, reference transfer, lifetime after peer exit, frame identity, reuse, stride/planes, completion/fences and release obligations. Static symbols, CPU locks and synthetic Mach handoff cannot establish native GPU completion semantics.

Produce a native protocol specification only from accepted observations, and retain unknowns. A portable WIT or equivalent contract is a new, separately named interface, with measured native mappings where available. Select sockets/shared memory or another portable mechanism according to the subset's actual ownership and performance needs rather than copying the original proposal blindly.

## Product implementation scope

Before I1, define the first supported platforms and source subset. The initial CLI should accept a fixture/project, build it, render one deterministic frame, save its image and emit a structured result. Add an interactive UI only after that pipeline works.

Core responsibilities: project/source discovery, build planning, cache identity, runtime loading, validated host imports, state/update model, layout, rendering, assets/fonts, image export, structured diagnostics, cancellation, isolation and cleanup. State, environment propagation, dynamic text, images, modifiers, interaction and animation enter the roadmap through measured feature contracts, not implied SwiftUI completeness.

Hot reload is part of the product milestone. Each source revision/build/frame needs a generation identity; delayed frames from superseded builds cannot overwrite the current canvas. Rebuild only affected inputs, debounce bursts, invalidate dependency-sensitive caches and cancel obsolete work. Preserve state only under a validated compatible migration; otherwise report a reset. Failed builds or traps retain the last accepted frame with current diagnostics. Test repeated edits, syntax-error/recovery, stale completion, assets changing during build and rapid cancellation. Benchmark this complete edit-to-frame path, not just WASM execution.

The research MCP controls analysis. A preview product MCP serves builds/renders/capabilities and must not expose arbitrary native execution through loosely validated parameters. C ABI/bindings need explicit allocation/free, opaque handle lifetime, thread-safety and error ownership. Broad Python/JS/Swift/Go/etc. wrappers wait until their underlying API stabilizes and a consumer needs them.

Do not fork xtool or build a custom Swift compiler backend unless F2 proves a specific blocker and an alternative path cannot meet the selected goal. Likewise, runtime engine, Canvas2D/software rasterizer, RPC, WIT and package choices stay provisional until their measured requirements are known.

## Verification and edge-case acceptance

| Layer | Required acceptance | Limits that remain explicit |
| --- | --- | --- |
| Evidence | Sealed artifacts and frozen sources match external manifest anchors | Integrity is not proof of capture completeness or semantic correctness |
| Codec | Exact bytes when promised; independent typed decode otherwise | A shared implementation or self-round-trip is not an independent oracle |
| Lifecycle | Measured causal ordering, identities, replies and ownership | PIDs/timestamps/addresses can vary; keep raw values and declare semantic mappings |
| Images | A/A stability and A/B sensitivity; exact files and exact pixels reported separately | Rendering tolerances are named tiers, never described as bit exact |
| Portable subset | Native/candidate differential corpus plus untouched holdouts | Report unsupported features and denominator; no universal equivalence claim |
| Failure handling | Injected malformed payloads, wrong types, stale IDs, lost/reordered events, traps, timeouts and peer exits are detected | Failure shrinking must preserve the same predicate |
| Platforms | Fresh installation and repeated runs on each claimed OS/architecture | Cross-architecture executable bytes are not expected to match |

Broader remaining cases: OS/Xcode/Swift ABI drift; ASLR/PAC and PID reuse; late hooks and missing events; cache/scheme errors; source/build races; float/date/Unicode conversion; concurrent sessions; asset and font loading; DPI/ICC/alpha; animation clocks; GPU/CPU synchronization; memory pressure; multi-plane formats; JIT/runtime traps; cancellation during every ownership phase; restart/reconnect; and leaked or prematurely released resources.

Use property-based/seeded controls, corpus expansion and fuzzing only at understood boundaries. Run native negative cases in owned bounded helpers. Keep a holdout set outside normal implementation feedback. Fault-inject the verifier itself; a checker that accepts a known wrong output cannot certify that boundary.

## Agentic execution, efficiency and operations

Continue the bounded serial loop: restore identities → choose one high-information hypothesis → run the smallest owned control → seal → compare → classify support/contradiction/inconclusive → index claim → choose a discriminating follow-up → publish eligible checkpoint. Independent workstreams are logical options, not a requirement to create additional agents or mutate shared tools concurrently.

Remaining toolkit hardening includes peer/rights accounting, capture-completeness checks, stale-result detection, error fingerprints tied to relevant preconditions, protocol/resource graphs, explicit experiment dependencies, final-report coverage denominators and reproducible target-version migration. Audit invalid historical runs rather than quietly promoting them.

Compute hashes, exact diffs, byte/pixel comparisons and shrinking locally. Retrieve small evidence pages by identity; inspect only the relevant symbols/functions. Cache by complete source/tool/target identity. Measure tokens, runtime, artifact volume and useful hypotheses resolved separately. Local tools being free does not imply free model inference. Renew session budgets explicitly; unchanged failure loops should select another discriminating experiment or independent ready work.

Keep code, reviewed queues, sanitized summaries and owned synthetic goldens in Git. Keep raw Apple binaries, decompilation, private captures and mutable workspaces local. Commit development checkpoints; fast-forward master only for reviewed verified milestones. CI can run portable/offline checks without Apple dependencies; native baselines need a separately configured macOS runner. Release provenance should anchor evidence independently of an editable branch.

## Milestones and stopping criteria

| Milestone | Completion gate |
| --- | --- |
| Next RE checkpoint | Receiver-first exit, release accounting and explicit reuse controls measured; failures retained |
| Native oracle | Stable accepted A/A and A/B output with declared capture tier; complete native lifecycle required for canvas claims |
| Portable feasibility | Small source fixture executes across the chosen portable boundary on a non-Apple target |
| First usable product | CLI source-to-image slice, bounded failures, explicit feature subset and independent compatibility report |
| Hot-reloadable canvas | Transactional reload, current-generation pixels, state policy, clear diagnostics and measured edit-to-frame results |
| Native interoperability | Accepted native envelopes and relevant attachments replay through the native adapter |
| Release candidate | Reproducible installation, platform tests, isolation/cleanup, documentation, stable consumer interfaces and measured cost/latency claims |

No reliable calendar estimate exists for native capture recovery or framework/compiler feasibility. Re-estimate after those gates, using measured experiment/build throughput. Spend early effort on unlocking them, not on broad wrappers or speculative infrastructure. A narrow passing product is a milestone; full SwiftUI compatibility, all platforms and universal bit-for-bit output are not implied by it.
