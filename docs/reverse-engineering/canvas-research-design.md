# Xcode Preview Canvas: research and clean implementation design

This plan governs investigation and research tooling. It does not authorize this exposed context to implement the reconstruction. The current repository combines investigation, owned controls and prior reconstruction work; it is not an approved clean implementation input. Neither hashes nor fresh model names repair shared-context exposure.

## Outcomes and architecture

Milestone 1 requires the existing GitHub reverse-engineering contracts, including actual Canvas lifecycle/transport, required resource ownership/completion semantics and independently reviewed native reference behavior. Milestone 2 requires the declared cross-platform WASM Canvas delivery contracts. The historical `workgraph.json` and roadmap keep their acceptance authority. The new graph adds research selection, provenance and role gates; it cannot close either milestone by counting experiments.

Use two graphs. A typed knowledge graph answers what evidence supports a claim for a particular target build and scope. A task DAG answers what output a job consumes, who can produce it, and what independent verifier must accept. JSON is sufficient at this scale; no external graph service, embedding API or database purchase is needed.

`research/loop/canvas-ontology.json` defines ten entity types and twelve domain/range constrained relations. Events are first-class: do not merge request, publication, completion, cancellation, release or process exit. Each node has a source path/hash, locator, extraction time, confidence category, target identity and scope. Relations retain their own source and confidence. Preserve source declarations, inferences, owned oracles, native UI observations and correlated native transport as separate grades.

The ten-document pilot contains 15 entities and five candidate relations. Its records are grounded in hashed historical documents; this is not independent semantic verification of their experiments. A separate reviewer must assess at least 50 entity/relation items at >=90% precision before broader extraction/fusion. Current semantic review remains pending. Exact duplicate fusion keys are rejected. Different OS/Xcode builds, process identities, resource identities and frame generations never merge merely because names or numbers coincide. Contradictions and failed controls remain visible.

## Research frontier

| Track | Discriminating control and acceptance | Boundary |
|---|---|---|
| Readiness | Pin target/REA identities, independently check private bridge and owned UI route; verify compiler descendant accounting and zero owned workspaces | REA availability is not capture readiness; no automatic bridge restart |
| Repeatable input | Same owned input repeated with positive and negative controls; correlate delivery with state and frames | Binding mutation is an oracle, not proof of actual Canvas click delivery |
| Refresh/state | Same-source refresh; same-identity edit; changed identity; error/recovery; stale binding and delayed completion | Distinguish retained state, reset, detached bindings and renderer recreation |
| Display/export | Same source/session/geometry captured via lossless export and display path; record ICC, scale, alpha and conversion | JPEG screenshot medians cannot establish native frame byte parity |
| Lifecycle/transport | Correlate actual Canvas request/reply, resource attachment, frame generation and completion in one session | Strings, selectors, synthetic Mach traffic and owned protocol models do not establish the native wire contract |
| R1 failure release | Before transfer, after import, before acknowledgement, timeout and peer-exit paths; actual waits and rights accounting | Missing observer rows are not proof of retirement; physical reclamation stays unknown until measured |
| R2 reuse/completion | Retained resource across new generations; delayed/stale consumers; observed completion/fences | Surface ID, Mach name and frame generation are distinct; CPU lock success is not GPU completion |
| Delivery parity | Required normal/edge/error behaviors on macOS, Linux, Windows and browser; edit-to-frame latency, restart and reconnect | A finite primary-color subset is not universal SwiftUI support |

Prioritize acceptance gate unlocked, discriminating power, independent evidence and cost. Consult the coverage lookup and sealed historical scopes before writing a new probe. Completed alias/use-count, source-read and callback controls are not fresh R1/R2 progress. A blocked capture route permits independent research that resolves a named acceptance uncertainty; unrelated adapter hardening must justify that dependency explicitly.

## Execution contract

One controller lock owns acquisitions and graph writes. Remain serial unless the user authorizes delegation. Resume unfinished owned wakes; do not create a second writer. A task's budget is charged before launch, never reset after failure. Declare the predicted difference, negative control, relevant byte domain and stop condition before acquisition. Native children must run through an owned supervisor that records descendant identities, bounded termination and actual waits. A timeout of a compiler driver alone is insufficient cleanup evidence.

For each Xcode session: verify generated workspace ownership, preserve user windows, use the existing approved bridge when live, close that workspace after success or failure, and verify zero owned windows before opening another. Do not terminate user Xcode/simulator processes, change protections, re-sign Apple applications or guess private Swift ABI.

Read-only inspection remains available. Legacy `graph-loop --execute` is now denied while the recorded clean-room boundary is active: its old bindings have not undergone role/scope review. The new planner deliberately does not launch processes or agents. Research adapters can be re-enabled only after explicit role/budget/ownership review, rather than blanket authorization inherited from old bindings.

## Independent verification and clean handoff

Investigator -> evidence verifier -> behavior specification -> specification reviewer -> isolated implementer -> delivery verifier. Investigator and specification author can be exposed to target internals; their internal analysis must never become implementation input. A separate reviewer checks externally observable requirements and public standards, not a pseudocode translation with renamed variables. Internal architecture is left to the implementer unless required by an observable interface.

The fresh implementer gets a new context and a separate workspace/repository containing only the reviewed package. No inherited chat, research `.git` history, research tools, decompilation, private dumps, recovered internal layouts or target-derived code. Enforce that access through actual workspace/tool permissions; a prompt or subagent in the same unrestricted checkout is insufficient. Existing reconstruction stays outside the package pending provenance audit. Assets require origin/license/attribution rows; unknown provenance is quarantined.

`canvas_graph.py handoff REVIEW NEW_DIRECTORY` validates an exact hashed file allowlist, independent author/reviewer context identifiers, behavior/provenance review, approved kinds/formats, attribution, safe paths and bounded size. It validates every file before writing and refuses existing destinations. The exported package excludes internal paths and review history. No package is currently approved. The exporter cannot prove reviewer independence, detect every semantic leak or enforce recipient permissions; those remain explicit external review/isolation obligations. It is a gate, not a clean-room certification.

Independent task acceptance must bind the exact output artifacts, full required-check set, grade, scope and distinct producer/reviewer contexts. Self-reported context identifiers are audit attestations, not cryptographic proof of isolation. Schema checks and tests performed here do not substitute for that independent review.

## Commands and next actions

```
python3 tools/re/canvas_graph.py validate
python3 tools/re/canvas_graph.py plan
python3 tools/re/canvas_graph.py plan --role evidence-verifier
python3 tools/re/coverage_lookup.py alias "use count"
```

The immediate investigator frontier is provenance inventory and evidence-coverage audit. Native readiness requires changed external prerequisites and verified compiler-descendant cleanup. Independent verification, spec approval, implementation and delivery remain gated. No completed research or milestone is silently promoted. Record exact blockers and stay quiet on unchanged wakes; do not fill time by repeating sealed probes.
