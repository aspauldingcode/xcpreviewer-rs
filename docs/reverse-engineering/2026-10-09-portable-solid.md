# First portable literal rectangle boundary

## Contract and measured result

The feasibility contract is deliberately small: a hand-authored C function fills opaque red or blue RGBA rectangles, width 1–320, height 1–160, stride from width×4 through 1280, into a fixed 204800-byte buffer. Explicit padding is `0xcd`. Invalid dimensions, stride or variant return zero without mutating output. This is a rendering ABI, not a Swift source parser or recovered Apple protocol.

Existing LLVM clang 21 emits wasm32 IR and links a no-import WebAssembly module with wasm-ld. llvm-objdump records module sections. Node 24.19.0 / V8 13.6.233.17 executes the module on this macOS host without Apple framework calls. Red/red/blue complete outputs match all 614400 decoded RGBA bytes from the independently sealed SwiftUI ImageRenderer oracle; A/A output is exact. A padded 3×2 control matches every explicit padding byte. Ten invalid calls preserve the entire fixed output buffer. No native fallback or new package/runtime installation is used in the execution path.

The adapter checks the native manifest against its trusted anchor before consuming snapshots and records LLVM/linker/module/source hashes, imports, exports and runtime identities. All 102 tests pass. The initial missing public adapter enum was caught, retained locally and synchronized before the final passing suite.

## Holdouts and next gates

Text, general colors, opacity/blending, nested layout, fonts, assets, state, animation, Swift syntax/type semantics, hot reload and performance are outside this first contract. No Linux/Windows/browser execution was performed. Complete SwiftUI or Canvas compatibility, Mach/GPU transport, completion and final reclamation are not established. F1 and both milestones remain open.

Next: choose a source-language or intermediate-representation boundary for this explicit subset; reject holdouts clearly and run another independent WASM runtime/browser before expanding features. A C rectangle alone does not make Apple app source portable.

## Skills selected

User-requested `reverse-engineering` and `llvm` guides were installed from commit-pinned Low-Level Dev Skills; `frida` from commit-pinned as0ler/skills. Installed Markdown hashes match reviewed files; source/provenance is in [skill registry](../../research/loop/skills.json). They are workflow guidance, not extra permissions or substitutes for measurements. Caveman FULL remains active for user-facing communication.

RE triage and LLVM IR/module-inspection workflows were applied here. Frida guidance is available for owned instrumentation, without retrying unchanged protected-process failures. Existing local Frida is 17.23.1; the upstream skill's claimed latest version is older, so API examples require local verification. No third-party skill examples or installation commands were executed.

See [sealed results and comparisons](../../research/evidence/portable-solid-2026-10-09.json). Run `20261009T164421Z-portable-wasm-solid-parity-6af2a478`; manifest SHA-256 `6e36035613cf64054e8bf54d39c59850dfed5c1ebd3b505277c19ee2c860d0f0`.
