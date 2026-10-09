# xcpreviewer-rs

Research toward a portable Swift view previewer. This repository begins with reverse engineering of Xcode's preview pipeline; it is not yet a working SwiftUI-to-WebAssembly renderer.

The proposed roadmap is in [plan.md](plan.md). Its dependency versions, protocol examples, and portability assumptions are proposals to validate against observed behavior.

`master` holds verified milestones; `development` holds ongoing investigation and implementation. Reverse engineering tools and findings land on `development` first, then verified milestones are merged into `master`.

Initial results are in [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md), with reproducible [research tools](tools/re/README.md) and a [progress log](PROGRESS.md). The first pass identifies XPC property-list adapters, native JIT loading hooks, and multiple rendering payload types on Xcode 26.6.

The [free agentic RE toolkit](docs/reverse-engineering/toolkit.md) adds a bounded experiment controller, stdio MCP server, GhidraVibe integration, Frida/LLDB tracing, native SwiftUI reference capture and immutable evidence. Its [loop design](docs/reverse-engineering/agentic-loop.md) separates working instrumentation from the remaining live preview protocol campaign.
