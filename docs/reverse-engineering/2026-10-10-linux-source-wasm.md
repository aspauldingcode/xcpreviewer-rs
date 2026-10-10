# Anchored source WASM on Linux ARM64

This experiment passes a narrow non-Apple operating-system execution gate for the [literal source subset](2026-10-09-literal-source-ir.md). Compilation remains on macOS; exact previously sealed standalone and diagnostic WASM modules execute in Linux. It does not establish a Linux compiler frontend, complete Swift programs, general SwiftUI, browser execution or Canvas transport.

## Host and runtime

An existing Colima VM was already running with Linux kernel `6.8.0-100-generic` on aarch64, using macOS Virtualization.Framework. The Linux operating system is virtualized on Apple hardware. A cached Linux ARM64 image, SHA-256 `4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109`, supplies Python 3.12.3. The adapter neither starts/stops the VM nor operates on its pre-existing user container.

The pinned [Wasmtime Python 49.0.0 Linux ARM64 wheel](https://pypi.org/project/wasmtime/49.0.0/) is staged in ignored research storage. The wheel is 8,853,040 bytes with SHA-256 `263b924576d9519c43d5a1acff50a03ab03209d16d26c53543c9ab9a409fb93f`. Download integrity, extraction paths/symlink safety and unpacked size were checked during provisioning. Before every execution the adapter verifies that hash, the complete extracted file inventory, and every extracted file against the wheel. No third-party runtime binary or Apple image is published. API usage follows the [official Wasmtime Python documentation](https://bytecodealliance.github.io/wasmtime-py/).

The repository is private. Actions are enabled but a free allowance was not established, so no paid-capable remote job was dispatched. Execution uses the existing local VM and cached image; the container has no network, read-only root, dropped capabilities, no new privileges, one CPU, 256 MiB memory and 64-process limit. Evidence/runtime/runner mounts are read-only; only the owned result directory is writable. No image pull is allowed. Each WASM store has a 1 MiB memory limit and each call receives a finite 100-million-fuel budget. The Docker call has a 45-second deadline within the exclusive controller's 120-second deadline.

## Independent byte and control evidence

Source modules are anchored to run `20261009T235049Z-portable-source-second-interpreter-668376cf`, manifest SHA-256 `db1ab482584b1fbf0d6e004cdc0197b35500d874663bbe153145446d4bde16f9`. Every standalone/diagnostic module hash is checked before instantiation, and all imports must be absent. Linux host/architecture and actual installed runtime version are checked, not substituted with macOS execution.

Four exact standalone modules render red, identical red, blue and padded 3x2 red. The Linux host directly reads each complete 204,800-byte allocation. Active output compares against anchored decoded native pixels or independent padded literals; unused bytes must preserve the separately assigned `0xa5` sentinel. Baseline comparisons cover 819,200 allocation bytes. Sixteen invalid strides preserve all 3,276,800 tested allocation bytes. Active frame dumps independently compare with the prior macOS V8 outputs across 614,432 bytes.

The four exact diagnostic modules additionally run all 40 full-buffer checker calls. Their results agree with the sealed WasmKit/V8 results, including 12 active/padding/unused-tail fault controls and out-of-domain checker arguments. Unlike the WasmKit CLI-only evidence, standalone Linux output is directly extracted and externally compared byte for byte.

## Cleanup, failures and publication

Each invocation uses a unique container name and a separate full ownership nonce label. Cleanup inspects that label before any forced removal, refuses an unowned container, and verifies zero remaining containers under the owned name. Both sealed runs pass. The existing user container was independently confirmed still running after cleanup. No Xcode windows opened and no user processes were terminated.

Four new tests cover unowned-container preservation, already-removed containers, owned removal, failed cleanup, and source-anchor/runtime-wheel rejection before Docker execution. The first full suite caught a missing `linux_wasm` entry in the campaign schema; that failure is retained locally and the schema is synchronized. The corrected full suite passes 227 tests. There are now 27 reviewed adapters; research MCP tool count remains 19.

Published evidence contains sanitized host facts, counts, hashes and anchors. Raw modules, third-party runtime files and local logs remain ignored. To reprovision, use the exact published wheel and digest above in `research/build/linux-wasmtime/wasmtime-49.0.0.whl`, extract safely into sibling `package/`, and record version/digest/download URL in `identity.json`. The adapter requires the existing cached image and VM; it never provisions or restarts them automatically.

The narrow Linux execution criterion now has acceptance evidence. Broader source/frontend/feature selection, Linux compilation, browser/Windows coverage, native Canvas IPC, runtime release/races, hot reload and performance remain open. F2 and both milestones remain open; this result does not promote the source-fragment experiment into a full cross-platform preview product.
