# Native Canvas recovery gate before standalone implementation

User requirement, 2026-11-01: Xcode Canvas must be fully reverse engineered first. This gate defines the required evidence structure; it does not declare the gate complete. The full product target is in product-goal.md and the per-project requirements are in omarchy-project-integration.md.

Pin the Xcode/SDK/OS/device versions for every native baseline. Inventory the shipped Canvas surface and its behavior from actual observations and recovered code. A proposed feature name or generic replacement behavior is not evidence that native Canvas implements it in that form. Keep source, runtime and original reconstruction policy separate.

## Required recovery areas

| Area | Required native evidence | Current qualification boundary |
|---|---|---|
| Canvas UI | Complete shipped control/mode inventory, enabled/disabled states, selections, menus/shortcuts and transitions. | Existing reconstructed viewer behavior is original policy; full native UI coverage is open. |
| Project binding | Workspace/project/target/scheme selection, source membership, dependencies, settings, resources and preview ownership. | Full native project binding is open. |
| Discovery and variants | Preview declarations, provider/registry discovery, traits, multiple previews and selection identity across edits. | Selected plain registry/body and explicit provider controls are qualified on pinned profiles; general Canvas discovery/variant flow is open. |
| Build and refresh | Native build planning, diagnostics, resume/update/cancel/failure/retry, invalidation and revision correlation. | Owned watch/follow behavior is useful but does not establish native scheduling/refresh parity. |
| Sessions and transport | Actual end-to-end Canvas/agent/host lifecycles, routing, callbacks, message fields and error paths. | Lower-level native connection/reply/codec observations remain scoped; integrated Canvas routing is open. |
| Rendering | Each required rendering route, layout/environment propagation, output ownership and publication/completion ordering. | Bitmap codecs and selected native render paths do not establish all routes or device rendering. |
| Interaction and state | Real events, focus/navigation/accessibility, view identity, state/bindings/observation, tasks, transactions and animations. | Full native interactive/state behavior is open. |
| Resource lifetime | Owner graphs and cleanup on success, failure, cancellation, refresh, reuse and peer loss. | Scoped surface/descriptor/callback controls do not establish universal final settlement. |
| Target differences | All applicable behavior above for each claimed Apple platform/device profile and host integration boundary. | No all-target parity claim is currently established. |

## Evidence required to close an area

- Source-backed entry points and state/ownership transitions tied to pinned shipped identities.
- Actual native observations with positive-change and relevant negative/failure controls.
- Explicit input/output/ordering contract and complete comparison at its declared scope.
- Reproducible replay or retained direct-observation procedure, including limitations, failures and unresolved cases.
- Coverage mapped to the original project, selected target and native version rather than a universal inference from one fixture.

A decompiler output, successful build, matched screenshot or isolated protocol exchange alone cannot close an area. Required unresolved behavior keeps the recovery gate open. A conformance model may be versioned and extended as Apple changes Canvas; that does not permit silently dropping any requested target from the end goal.

## Active research priority

Recover actual Canvas project/preview binding and observable UI/session/refresh transitions, and use them to direct the remaining native analysis. Continue lower-level transport/resource work when it closes a named required gap. Toolchain/source feasibility and reusable upstream components can be evaluated in preparation, while the full standalone Canvas implementation remains dependent on this recovery gate.

This gate supplements the existing milestone contracts and preserves all prior scoped evidence. Both delivery milestones and the full product goal remain incomplete.
