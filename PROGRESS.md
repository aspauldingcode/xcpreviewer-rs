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

Not yet implemented: Rust preview core, SwiftUI compatibility layer, WASM compilation/runtime, renderer, bindings, or MCP server. Nothing in this milestone establishes end-to-end preview compatibility.
