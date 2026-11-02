# Product goal: a liberated SwiftUI Canvas

User clarification, 2026-11-01:

> the end goal is making development of any swiftui application for any apple device 1:1 experience on any other system with a liberated, wasm-based xcode preview canvas

This is the product destination. A supported subset is an implementation checkpoint, and every unsupported feature is unfinished coverage toward that destination. A Mac renderer feeding a portable bitmap viewer does not satisfy the execution requirement. Existing native/protocol work remains evidence for reconstruction, with its original limited claims.

## Required developer experience

Open real SwiftUI project source on a non-Apple host, build its preview, select the intended Apple device/environment, interact with it, edit code, inspect errors and see the update with the state/lifecycle behavior of the native Canvas. The reconstructed Canvas UI/control/session application and preview runtime execute through our WASM-based product. Thin host adapters supply platform facilities. Full native Canvas reverse engineering is required before starting the standalone replacement implementation. Existing prototype components remain preparatory research. The normal build/render/interaction path must work without a Mac service, Xcode, simulator or Apple frameworks running elsewhere. Apple systems remain reference oracles during research and conformance testing.

The target covers iOS, iPadOS, macOS, watchOS, tvOS and visionOS device families, the user-requested iPhone Duo profile label and additional future targets. Exact device identifiers/behavior require verified SDK/native profiles. Versions and configurations must be explicit, so claims are testable against pinned native behavior and new platform releases create visible compatibility work. Host support must be verified on actual non-Apple systems; a WASM target compiled and executed on a Mac alone is insufficient evidence for Linux, Windows or other hosts.

The intended input is application SwiftUI source and its real dependencies/resources. Replacing the app with a hand-authored scene, recognizing a few expressions with a text parser, or displaying a native screenshot can establish component feasibility but cannot establish general SwiftUI execution. Project/module resolution, macros, resources, concurrency and platform integration belong in the coverage contract.

## Meaning of 1:1

Acceptance includes visual output, layout/measurement, text shaping, view identity, state/bindings/observation, transactions/animations, tasks/lifecycle, event routing, focus/navigation, accessibility, environment/traits and code-refresh behavior. Device-specific input and presentation include touch, pointer/keyboard, remote focus, crown and spatial interaction where applicable. Platform-hosted views and system capabilities require explicit implementations or host adapters with measured behavior; silent stubs and hidden native fallbacks do not count as parity.

Deterministic native fixtures require complete matching outputs. Any allowance for native variability must be demonstrated, attributed and scoped; it cannot hide reconstruction errors. Transition sequences and resource/error/cancellation behavior must be compared in addition to initial frames. Developer responsiveness needs measured latency budgets and failure recovery on each claimed host profile.

A compiler success, decompiler result, bitmap match, protocol subset or passing example does not close the full goal. Keep a versioned feature/device/host matrix, application corpus and unresolved-gap register. Existing milestone/issue contracts remain recorded; subset issue completion is never substituted for full product acceptance.

## Present boundary, 2026-11-01

The repository has recovered native payload/protocol/resource behavior, a Rust/WASM bitmap viewer, a bounded primary-layer source path, a Mac SwiftUI source producer and source-watch/browser-follow workflows. The SwiftUI producer still uses native compilation and ImageRenderer on a Mac. The Rust WASM display path does not execute arbitrary SwiftUI applications.

A direct local toolchain check now establishes ordinary Swift 6.3 source compilation with the installed WASIp1 SDK and execution through Node WASI, with an independently expected counter output of 0, 1, 2. A separate SwiftUI state/button fixture fails with no such module SwiftUI. These are Mac-hosted build/execution checks, not a non-Apple host result. This identifies the absent compatible SwiftUI module/runtime as a concrete dependency. See the [portable Swift goal evidence](../research/evidence/portable-swift-goal-2026-11-01/README.md); no new private framework call or native Canvas parity is claimed by that check.

## Execution order

1. Complete [native Canvas reverse engineering](canvas-recovery-contract.md), including its UI, project binding, discovery/variants, build/refresh, session/transport, rendering, interaction/state, resources and target-specific behavior. Required unknowns keep this gate open.
2. Derive and validate [per-project integration](omarchy-project-integration.md). Evaluate the user-authorized omarchy-apple-dev foundation for build/project/device tooling; its existing coverage does not establish our all-target Canvas contract.
3. Implement our standalone Canvas UI/session/runtime in WASM around the recovered contracts. The compiler/toolchain and host adapters must preserve each actual project's selected target semantics and dependencies. Native deployment and WASM preview are distinct associated build products.
4. Qualify the complete persistent compile/render/interact/update workflow against native references, then close feature/device/host coverage without silently excluding unsupported requested targets. A small interactive slice remains an intermediate checkpoint, with the native recovery gate first.

Ordinary Swift-to-WASM feasibility and existing render/protocol components remain useful preparatory evidence. The previous local missing SwiftUI module result is not a claim that no reusable compatibility work exists elsewhere. Upstream simulation/build work must be evaluated at its measured scope and native parity verified independently.

Active priority is completing the native Canvas behavior/project-binding model before the standalone replacement. Existing milestones and the full end goal remain incomplete. Publication approval and the prohibition on publishing Apple binaries/private dumps remain unchanged.
