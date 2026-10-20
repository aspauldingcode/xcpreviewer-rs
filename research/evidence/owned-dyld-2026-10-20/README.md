# Owned dylib observation and crash-report consumer frontier

A new original research dylib interposes public CGImageCreate, CGImageRetain and CGImageRelease in newly launched owned executables. This changes the observation method after the earlier Frida attach cancellations. It does not attach to, restart, modify or inject Xcode, and establishes no Xcode injection permission or private Canvas runtime parity.

## Discriminating runtime controls

The disabled-injection negative produces no trace. Four enabled controls load the observer (independently present in dyld's library listing), correlate every event PID with the actual owned child PID, and observe creation entry, nonnull return, release entry and release return on the same handle. All56 output bytes match the uninstrumented host and frozen independent expectation, including16 row-padding bytes and16 tail bytes. These frozen inputs/expectations come from the prior bitmap-image experiment; they test instrumentation preservation here, not additional format coverage.

A changed ownership control adds one explicit retain and an extra release. The observer records the retain entry/return and both release entry/return pairs on that same handle; all56 output bytes remain identical. A zero-width negative observes synchronous CGImageCreate returning NULL and no image release. No timeout, process exit or successful stdout substitutes for these API observations. Calls returning do not establish final deallocation, private operation settlement, no-later-effect, IOSurface/Mach ownership, fences, or Canvas cleanup.

Four deliberately corrupted traces (absent trace, absent release return, wrong handle, wrong PID) are rejected by the verifier. replay.py rebuilds with existing clang, runs all6 controls with30-second subprocess deadlines, compares every byte and tests those verifier mutants. It acquires the controller lock; only its own newly launched child can be killed on timeout. A deadline failure remains a failure, never a passing settlement receipt. Raw pointers and dyld paths stay local. Published files are original source, synthetic input/output expectations and sanitized results; no dylib/executable or Apple code is published.

```sh
python3 research/evidence/owned-dyld-2026-10-20/replay.py /private/tmp/FRESH-OWNED-DYLD-RESULTS
```

## Recovered source frontier

A bounded named-symbol search of four additional preview frameworks identifies CrashReportService in PreviewsPlatforms and report presentation/state consumers in PreviewsUI and PreviewsScenes. A search without matches in PreviewsXcodeUI does not prove absence of consumers. Selected Ghidra functions recover the service's cached-Future branch and typed async request setup. The first resume constructs NextCrashRequest(process:timeout:) and awaits the daemon connection. source-findings.json records addresses, sizes, pinned SHA and limitations. Raw decompilation and ARM64 instructions stay local. No guessed private Swift ABI declaration or direct call is introduced.

The service is a concrete next source boundary, not a captured transport or the actual view-input path. Recover its remaining send/reply/error/cancellation continuations and CrashListenerInterface message structure next, then correlate runtime observations in an owned compatible host if existing permissions allow. Do not infer that diagnostic-request timeout settles the original preview operation. Do not repeat the old unchanged Frida attachments. R1, R2, native capture and both milestone acceptance contracts remain open.

The prior report-model seal and every member were reverified. REA6.2.0 identity/alignment and the selected ARM64 target were checked; GhidraVibe0.1.1/engine5.14.2 were reused. REA and analysis locks were closed. No Xcode workspace was opened, so no user workspace required closing. Source/runtime/transport claims remain separate.
