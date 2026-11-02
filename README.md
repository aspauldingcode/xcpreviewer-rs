# xcpreviewer-rs

Follow the [live progress dashboard](https://aspauldingcode.github.io/xcpreviewer-rs/) for overall delivery, milestone tracking, native recovery acceptance and remaining work.

Research toward a portable Swift view previewer. This repository begins with reverse engineering of Xcode's preview pipeline; it is not yet a working SwiftUI-to-WebAssembly renderer.

The [product goal](docs/product-goal.md) is a 1:1 SwiftUI Canvas development experience for any Apple device on other systems through WASM. Supported subsets and native frame producers are intermediate checkpoints toward full compatibility. Full native Canvas recovery comes first; [project integration](docs/omarchy-project-integration.md) must preserve each real project’s target, settings, dependencies and resources.

A [supported source-to-frame CLI](docs/reverse-engineering/source-frame-cli.md)
now builds explicit primary-layer expressions into WASM, verifies their complete
frame allocation and publishes a PNG while preserving the last good result on
failure. Try the [sample source](examples/primary-layers.swift).

[Canvas examples](examples/CanvasExamples/README.md) provide an owned Xcode project
for color edits, text and button state, and layout changes. The
[native editing comparison](docs/reverse-engineering/canvas-edit-comparison.md)
records measured behavior and remaining reconstruction gaps.

The proposed roadmap is in [plan.md](plan.md). Its dependency versions, protocol examples, and portability assumptions are proposals to validate against observed behavior.

The current [remaining-work plan](docs/remaining-work.md) orders native capture, protocol/resource recovery, portable feasibility, implementation and acceptance by their actual dependencies.

GitHub delivery tracking: [0 → Reverse-engineered](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/1), then [Reverse-engineered → Fully cross-platform WASM canvas](https://github.com/aspauldingcode/xcpreviewer-rs/milestone/2). Both milestones remain open; issue completion measures their declared acceptance gates.

`master` holds verified milestones; `development` holds ongoing investigation and implementation. Reverse engineering tools and findings land on `development` first, then verified milestones are merged into `master`.

Initial results are in [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md), with reproducible [research tools](tools/re/README.md) and a [progress log](PROGRESS.md). The first pass identifies XPC property-list adapters, native JIT loading hooks, and multiple rendering payload types on Xcode 26.6.

The [free agentic RE toolkit](docs/reverse-engineering/toolkit.md) adds a bounded experiment controller, stdio MCP server, GhidraVibe integration, Frida/LLDB tracing, native SwiftUI reference capture and immutable evidence. Its [loop design](docs/reverse-engineering/agentic-loop.md) separates working instrumentation from the remaining live preview protocol campaign.

Exact-output acceptance, evidence anchors, edge-case automation and AI porting strategy: [verification contract](docs/reverse-engineering/verification.md).

Recursive findings: [local XPC coding, malformed-input boundary and static message strings](docs/reverse-engineering/2026-10-08-xpc-boundary.md), followed by [raw coder controls and owned surface lifetime](docs/reverse-engineering/2026-10-08-raw-coder-surface.md).

Latest checkpoints: [owned surface handoff across processes and sender-exit lifetime](docs/reverse-engineering/2026-10-09-surface-ipc.md), then [receiver-first exit, local right counts and retained-port access](docs/reverse-engineering/2026-10-09-surface-receiver.md).

[Continuous RE operation](docs/reverse-engineering/continuous-loop.md) now uses a ten-minute desktop heartbeat in the existing chat, with a [durable work checkpoint](research/loop/continuous.json). Local scheduling requires the computer and desktop app to remain running; the loop advances experiments and implementation, then synchronizes verified progress.

Latest recurring-loop findings: [failed handoff cleanup and surface recycling state](docs/reverse-engineering/2026-10-09-surface-failure.md).

Further recurring-loop findings: [delayed surface reuse and repeatable native ImageRenderer references](docs/reverse-engineering/2026-10-09-reuse-renderer.md).
