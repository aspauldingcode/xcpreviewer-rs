# Reproduce the preview investigation

Requires macOS, an installed Xcode, its command-line tools, and Python 3. No extra dependencies are needed for collection or runtime probes. Run from the repository root.

## Automated experiments and MCP

See the [free toolkit guide](../../docs/reverse-engineering/toolkit.md) for bootstrap, local Ghidra service lifecycle, the eight-experiment queue, MCP client configuration, Frida/LLDB probes and evidence verification. The manual commands below remain useful for targeted investigation.

The reviewed connected campaign includes local XPC corpus, malformed-envelope and prefix/shrinking experiments plus bounded static message-string recovery. See [findings](../../docs/reverse-engineering/2026-10-08-xpc-boundary.md) and the synthetic [XPCOracle](fixtures/XPCOracle/manifest.json). These do not establish live service traffic or attachment compatibility.

Further reviewed controls measure raw-coder key/class behavior, local IOSurface holder/reference lifetime with exact row-padding bytes, and the deferred canvas hook on an owned helper. See [results and limits](../../docs/reverse-engineering/2026-10-08-raw-coder-surface.md) and [SurfaceOracle](fixtures/SurfaceOracle/manifest.json).

The `surface_ipc` adapter transfers an owned IOSurface Mach right between audit-verified fork/exec peers and checks clean/abrupt sender exit, retained bytes and temporary rendezvous cleanup. See [findings](../../docs/reverse-engineering/2026-10-09-surface-ipc.md) and [SurfaceIPCOracle](fixtures/SurfaceIPCOracle/manifest.json). Actual canvas XPC envelopes and GPU fences remain open.

Set `surface_ipc` parameter `exit_order` to `receiver` for clean/abrupt receiver-first exit, local send-right counts and retained-port access after original owner CF release. See [receiver-first findings](../../docs/reverse-engineering/2026-10-09-surface-receiver.md) and [SurfaceReceiverOracle](fixtures/SurfaceReceiverOracle/manifest.json). Failure/timeout cleanup and final kernel reclamation remain open.

## Static collection

```sh
python3 tools/re/collect.py
```

An alternative Xcode installation can be selected with `--xcode /path/to/Xcode.app`. The script uses that installation's developer tools. Outputs go to ignored `research/raw/`: an inventory with SHA-256 fingerprints, load commands/UUIDs, exported symbols, demangled signatures, strings, and OS SDK stub exports. The messaging framework also gets a complete local symbol table for private key witnesses.

The collector does not extract the dyld cache or copy Apple executables into the repository.

## Runtime metadata and synthetic serialization

```sh
sh tools/re/dump-runtime.sh
```

Use `XCODE_APP=/path/to/Xcode.app` for another installation. The helper binaries and compiler caches stay in `research/build/`; results go to `research/runtime/`.

The Objective-C helper loads requested preview libraries and enumerates their classes, methods, adopted protocols, matching named protocols, and loaded-image UUIDs. Library initializers execute as part of `dlopen`; the metadata helper does not invoke private preview methods or connect to services. Pure Swift structs, enums, and protocol descriptors are outside ObjC enumeration.

The serialization helper invokes `UVPropertyList` only on a locally constructed dictionary and verifies round trips through both that class and Foundation. It makes no XPC connection. The Swift helper calls two exact exported key getters using Swift's ABI. Its symbols are specific to the observed framework version; a link failure on a different version is evidence to update the probe, not a reason to guess an ABI.

Host and OS Foundation variants are loaded in separate processes to avoid duplicate ObjC class registrations.

## Targeted disassembly

```sh
python3 tools/re/disassemble.py --query 'MessageTypeKey.getter|OneWayMessageKey.getter'
python3 tools/re/disassemble.py --query 'BitmapDescription.*Key.*rawValue.getter|RenderPayload.*PropertyListKey.rawValue.getter|LayerHostPayload.*PropertyListKey.rawValue.getter'
python3 tools/re/disassemble.py --query 'JITLoadCommand.*Key.*rawValue.getter'
```

This matches demangled names, then disassembles their original symbols using Xcode's ARM64 disassembler. `--binary` selects a different messaging image. Full function output remains local under `research/raw/disassembly/`.

## Ghidra

An existing Ghidra 12.1.2/GhidraVibe installation was used for this investigation. The Java script is usable with an ordinary compatible headless Ghidra installation too. Select a supported JDK for your installation. On this machine, the existing GhidraVibe guidance selects Semeru/OpenJ9 21.

```sh
mkdir -p research/ghidra/projects
/path/to/ghidra/support/analyzeHeadless \
  research/ghidra/projects PreviewsResearch \
  -import /Applications/Xcode.app/Contents/SharedFrameworks/PreviewsMessagingHost.framework/PreviewsMessagingHost \
  -max-cpu 2 -analysisTimeoutPerFile 120 \
  -scriptPath tools/re \
  -postScript DumpPreviewFunctions.java \
  "$PWD/research/ghidra/messaging-decompiled.txt" \
  9661c 96600 4aaf4 8d740 8e008 8e048 6fefc
```

Addresses are unslid hexadecimal addresses in the observed arm64 image, not runtime ASLR pointers. Resolve symbols again for another build. This installed image is already a thin arm64 Mach-O; do not blindly run `lipo -thin` on it. Repeat analysis on an existing project using Ghidra's `-process` option rather than importing over it.

Ghidra output is an analysis aid. Swift calling conventions, generic metadata, and optimized closures can produce misleading C pseudocode; compare with original instructions and runtime probes.

## Publishable evidence index

After collection and runtime probes succeed:

```sh
python3 tools/re/summarize.py
```

This generates a small index with image identities, selected signatures, relevant ObjC adapters, and synthetic probe results. Review the version-specific filename and findings before committing. Full Apple binaries, extracted caches, raw symbol tables, and decompiled implementation output are ignored by Git.

The `surface_failure` adapter measures three owned handoff fault stages; parameter `control: use_state` selects independent local/global surface use-state controls. See [fault and recycling findings](../../docs/reverse-engineering/2026-10-09-surface-failure.md). Final reclamation and actual Canvas reuse/ordering remain open.

The `surface_reuse` adapter compares delayed reads through reused/separate owned CPU surfaces. `native_reference` parameter `repeat_control: true` selects fresh-process ImageRenderer A/A and controlled text A/B. Both are separately scoped in [findings](../../docs/reverse-engineering/2026-10-09-reuse-renderer.md); neither recovers Canvas completion or hot reload.

The `xcode_bridge_probe` adapter bypasses discovery with a bounded direct read-only window-list call, explicit installed-Xcode selection and fresh session identity. Its capped message trace stays local. Initialization does not establish tool or Canvas readiness; the planner requires a changed prerequisite before retrying a timeout. See [direct-route findings](../../docs/reverse-engineering/2026-10-09-xcode-bridge.md).

Use `research/venv/bin/python tools/re/agent.py xcode-bridge start` once for an explicitly approved connection; `status` inspects ownership/listening state and `stop` terminates only the owned broker. The private Unix-socket broker retains approval across callers without global settings or added packages. `xcode_bridge_probe` with `managed: true` and Canvas capture reuse it; missing/broken service fails closed rather than silently creating another prompt. Access reuse is limited to the live broker/Xcode lifetime. [Access findings](../../docs/reverse-engineering/2026-10-09-xcode-access.md) explain the rejected chrome-only snapshots and unverified private preference candidates.

Close each generated Xcode workspace through the UI when its experiment ends, before another capture. The adapter records the cleanup target and refuses to open a new workspace while a prior generated one remains. Preview variants 2/3 are explicit sRGB solid red/blue; their exact center-patch control isolates non-text rendering. `native_reference` with `solid_control: true` compares entire separate ImageRenderer RGBA frames to independent literals, including alpha. Neither substitutes for text, full Canvas frame or wire acceptance.
