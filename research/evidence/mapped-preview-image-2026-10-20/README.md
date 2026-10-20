# Bounded mapped-preview-image analysis route

The macOS XCPreviewAgent executable is a launcher/JIT stub; its strings and SDK exports do not supply agent-side capture implementation. PreviewsInjection resolves to a system dyld-cache image with no standalone dylib file. The installed GhidraVibe find/resolve MCP tools confirm the cache/install path. MCP import lacks its helper in server PATH. Calling the existing helper explicitly with the working Java/runtime reaches the image but fails after55.652s at2G heap while expanding cache-wide slide fixups. No larger-heap or unchanged import retry occurred.

## Implemented alternative

Original map_image.c loads only PreviewsInjection in a newly owned process, enumerates its Mach-O image UUID/segments and reads only readable selected segments via mach_vm_read_overwrite on mach_task_self. It excludes LINKEDIT, caps each segment32MiB,total64MiB,32 segments and checks all read lengths. Three exported C bridge addresses are resolved through dlsym and independently read for32 bytes each. The explicit entrypoints are never called. dlopen can run library initializers; this is not represented as passive metadata with zero runtime effects.

replay.py compiles under warnings-as-errors with30s deadline and runs the newly owned child with15s deadline, under the exclusive controller lock. It emits a local ARM64 ELF analysis view with original mapped virtual addresses, explicit program/section headers and segment alignment1. Live pointers/data remain rebased, ASLR addresses are process/boot scoped and LINKEDIT is omitted. This is not an original disk Mach-O, standalone framework, executable reconstruction or private Swift ABI declaration.

Runtime UUIDc1a5cfb75f9935948e7004d4134de878 identifies the selected image. Its6 readable mapped segments total686,920 bytes. Every segment byte maps exactly into the generated container. All96 bytes independently probed through dlsym equal their enclosing segment/container bytes; independent LLVM disassembly succeeds. GhidraVibe imports the708KiB-class container without cache-wide fixups; imported memory at all3 probes matches all96 native bytes. Three deliberate container faults (changed code byte, truncated headers, wrong virtual mapping) are rejected. verified-mapping.json records exact V2 hash and relative unslid export addresses. Raw bytes, disassembly and decompilation stay local.

Two entry bridges were decompiled in the first sectionless profile, with PIC/removed-block warnings and unmapped external-target names. No private-call prototype or behavioral parity is inferred. The initial sectionless container imported in Ghidra but LLVM had no executable section; V2 adds sections and independent byte/disassembly checks. Optional Capstone was absent; existing LLVM was used. No package purchase/install or service restart was needed. Both container profiles and failures remain attributed locally.

## Failure retention and scope

The failed owned JVM unexpectedly generated about9.6GB of binary core/heap diagnostics. Those exact owned files were quarantined, attributed by name/size/prefix hash and removed to restore the artifact budget. Full textual JVM diagnostics, trace/logs, original commands and the exception stack are retained locally. No unrelated file or user process was removed. diagnostic-retention.json distinguishes removed binary dumps from retained diagnostics. Raw-provenance hashes cover retained files only; partial dump hashes are explicitly prefix hashes.

Prior evidence seal/members were reverified. Existing Ghidra engine identity and REA6.2.0 alignment were checked; owned importer exited with failure, mapped hosts returned successfully and acquisition locks/REA session closed. Process exit does not prove any private target operation settled. No Xcode MCP/bridge, Xcode attach/injection/restart/workspace, Apple re-signing/protection change or user-process termination occurred.

The adapter is research-only. It proves a feasible route to actual selected runtime code, not Canvas capture, protocol/cancellation/resource semantics, product compilation or milestone completion. Existing61 Rust tests were not rerun because product code was unchanged. Next use this bounded route to trace PreviewsInjection handoff into capture services and select the actual producer implementation; expand the adapter only for a concrete next target, preserving UUID/profile provenance. Source/native wire/GPU completion acceptance remains open.

```sh
python3 research/evidence/mapped-preview-image-2026-10-20/replay.py /private/tmp/FRESH-LOCAL-MAPPED-IMAGE
python3 research/evidence/mapped-preview-image-2026-10-20/verify_container.py /private/tmp/FRESH-LOCAL-MAPPED-IMAGE
```

Generated output contains Apple image bytes and must remain local. Publish only this original reader/mapper/verifier and sanitized findings.
