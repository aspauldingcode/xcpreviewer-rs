# Cross-platform project integration and the standalone WASM Canvas

User direction, 2026-11-01: omarchy-apple-dev may provide a development foundation; our standalone Canvas must integrate with each real project, reproduce Xcode Canvas UI/behavior in WASM and ultimately cover every requested Apple target. Full native Canvas reverse engineering is the prerequisite for the replacement implementation.

## Reviewed foundation

Repository: https://github.com/joshuaswarren/omarchy-apple-dev

Reviewed revision: `7bc44ea917e5f1fcd39c066346d43f827b5796f3`. Six source/document files were fetched and hashed. No upstream script was executed, installed or copied into the product. These are static observations and upstream reports, not independent build/device validation.

The [project importer](https://github.com/joshuaswarren/omarchy-apple-dev/blob/7bc44ea917e5f1fcd39c066346d43f827b5796f3/tools/xcodeproj2xtool.py) parses project.pbxproj and xcconfig inputs and generates an xtool/SwiftPM adapter tied to project source/resources. Its reviewed platform table contains iOS and macOS. Its platform selector falls back to iOS outside the macOS branch; that cannot serve as our all-target classifier. Treat it as a candidate for audited reuse, with unsupported cases explicit in our adapter.

The [simview documentation](https://github.com/joshuaswarren/omarchy-apple-dev/blob/7bc44ea917e5f1fcd39c066346d43f827b5796f3/simview/README.md) describes its own SwiftUI module and input/render model and explicitly disclaims real SwiftUI layout/font/animation/Metal parity. It offers implementation reference material, with native conformance still required. The [no-Xcode mode](https://github.com/joshuaswarren/omarchy-apple-dev/blob/7bc44ea917e5f1fcd39c066346d43f827b5796f3/sdk-free/README.md) is explicitly limited; its [test matrix](https://github.com/joshuaswarren/omarchy-apple-dev/blob/7bc44ea917e5f1fcd39c066346d43f827b5796f3/docs/TEST-MATRIX.md) distinguishes builds from actual device runs. The [MIT license](https://github.com/joshuaswarren/omarchy-apple-dev/blob/7bc44ea917e5f1fcd39c066346d43f827b5796f3/LICENSE) requires retaining notices if code is later copied/adapted.

## Layer responsibilities

- Cross-platform project/build adapters obtain the real project's resolved compilation inputs and, where requested, its native deployment product. Omarchy/xtool is a candidate backend. Additional hosts and Apple platforms require their own measured adapters.
- The reconstructed Canvas application owns its UI, controls, sessions and behavior in WASM. Thin host adapters provide windows/surfaces, filesystem access, process invocation and input. The current HTML/JavaScript bitmap viewer with a WASM decoder is an intermediate surface, not completion of the WASM Canvas UI requirement.
- The portable preview runtime executes the project's application/UI behavior using a compatible implementation. Producing an Apple-target native app and producing an executable WASM preview are distinct build results from a consistent project model; success of one does not prove the other.
- Native Apple systems supply reference observations during research and acceptance. Normal product operation on another host must not secretly call a Mac renderer or simulator.

## Required per-project binding contract

These are requirements to recover and validate, not an implemented importer specification. Actual Xcode behavior determines the final mapping.

| Boundary | Required information and behavior |
|---|---|
| Project identity | Original workspace/project/package root and stable project identity; adapters stay associated with the real source tree. |
| Build selection | Explicit scheme, target/product identity, configuration, selected destination and SDK/deployment context. Never infer every target as iOS. |
| Target membership | Actual source membership, generated sources, dependent targets, companion apps and extensions; distinct targets cannot share accidental preview state. |
| Settings | Resolved xcconfig/build-setting layers, search paths, compiler/linker arguments, build conditions and relevant environment. |
| Platform semantics | Apple target identity is separate from WASM execution target. Conditional compilation, availability and platform imports must preserve intended project semantics rather than changing because the preview host is Linux, Windows or WASI. The lowering mechanism remains unqualified. |
| Dependencies | Resolved module/package graph, versions/revisions, macros/plugins and native interoperability requirements. Unsupported dependencies produce actionable diagnostics. |
| Resources | Asset/localization/font/model/bundle ownership, generated resources and lookup paths matching the selected product. |
| Preview declaration | Selected source/declaration, registry/provider and variants within the precise build fingerprint. Compiler-generated registry names are not assumed persistent across edits. |
| Live revisions | Source, settings, dependency and resource changes invalidate the relevant build/preview revision. Stale frames must not cross project, target or declaration boundaries. |
| Diagnostics and refresh | Errors resolve to original source; build/cancel/retry/state-preserving or resetting refresh behavior follows the recovered Canvas model. |
| Native deployment | Device build, signing/install/debug products remain associated with the same project selection. Preview success alone never proves device deployment. |

A generated adapter directory is acceptable only while it accurately follows the original project. Requiring users to maintain a separate demo or manually duplicated source tree does not satisfy this contract. Adapter changes must preserve user project files and unrelated build work.

## Target coverage

The requested families are Mac, iPhone, iPad, Apple Watch, Apple TV and Apple Vision Pro, plus the requested iPhone Duo label and additional future targets. Use an extensible SDK/device-profile catalog with explicit native baselines and unresolved entries. The iPhone Duo label records user-requested coverage; no verified SDK identifier, hardware geometry or release status is asserted here.

Each target requires appropriate layout/environment, input, runtime, resources and platform API conformance. Shared source or a shared device label does not establish shared behavior. Track build, preview render, interaction, refresh and native deployment independently for each host/target pair. Omarchy's currently reviewed platform table does not define or limit our final target scope.

## Research and implementation order

1. Complete the [native Canvas recovery contract](canvas-recovery-contract.md), including project binding and platform-specific behavior. The standalone replacement cannot be called fully reverse engineered while required unknowns remain.
2. Derive the verified project model and audit upstream adapter reuse against native project/build observations. Preserve license notices for any actual adaptation.
3. Implement our WASM Canvas UI/session/runtime around that model, with bounded host adapters and no hidden Apple-host execution dependency.
4. Validate complete developer workflows against native references on every claimed host/Apple target. Subset demos remain intermediate checkpoints.

No current claim of full project import, full target support or Canvas parity is made. Publication approval requirements and the prohibition on publishing Apple binaries/private dumps remain unchanged.
