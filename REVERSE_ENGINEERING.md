# Xcode preview reverse engineering

The first investigation targets **Xcode 26.6 (17F113)** on **macOS 26.5.1 (25F80), arm64**. Findings are version-specific.

- [Observed architecture and protocol findings](docs/reverse-engineering/2026-10-08-initial-findings.md)
- [Reproduction instructions](tools/re/README.md)
- [Evidence index: image UUIDs, hashes, signatures, runtime metadata, synthetic probes](research/evidence/xcode-26.6-macos-26.5.1.json)
- [Free automated toolkit and setup](docs/reverse-engineering/toolkit.md)
- [Toolkit validation: eight experiments and evidence hashes](research/evidence/agentic-toolkit-2026-10-08.json)
- [Full agentic loop design](docs/reverse-engineering/agentic-loop.md)
- [Progress and next experiments](PROGRESS.md)

This is evidence gathering, not a working replacement for SwiftUI or Apple's preview engine. The WIT and C API in the original plan remain proposed interfaces. They are not recovered Apple protocol definitions.
