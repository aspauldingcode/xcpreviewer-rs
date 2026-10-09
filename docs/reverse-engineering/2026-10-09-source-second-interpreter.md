# Source-derived renderer in an independent interpreter

Extends the [literal source contract](2026-10-09-literal-source-ir.md) with WasmKit verification. It retains the strict explicit sRGB expression subset and separately anchored native ImageRenderer oracle. Native Canvas instrumentation and full-image REA import remain blocked without a changed prerequisite; this is an independent feasibility track.

## Checked boundary

Four accepted source fragments produce red, identical red, blue and a 3x2 padded red fixture. After the standalone V8/native/literal controls, the adapter verifies each saved renderer LLVM IR hash before linking that unchanged IR with a separately compiled checker object. Compilation uses separate translation units and no LTO. The checker uses externally decoded native pixels for the three full frames and independently predicted literals/padding for the small frame, rather than renderer-produced expectations.

The resulting four diagnostic modules are new modules, not byte-identical to the standalone modules. Each exact diagnostic module executes in both WasmKit and V8. They import no host functions. Source/renderer IR, expected-array and diagnostic module hashes, WasmKit binary identity/version, and V8/Node identities are retained. Typed `i32:` CLI arguments and a bounded single-result parser are required; ambiguous, malformed and wrong-type results reject. No native fallback or interpreter memory-dump claim is made.

## Whole allocation, rejection and fault controls

The checker verifies capacity equals 204,800 bytes, fills every byte with `0xa5`, calls the renderer with the supported stride, then compares the entire allocation. Active output must equal the independent expected array, including `0xcd` row padding. Bytes beyond the active output must remain `0xa5`. This strengthens the prior active-frame comparison by measuring preservation outside the frame.

Per module, baseline must report zero mismatches. Three injected faults flip the first active byte, last active byte and last allocation byte; each must report exactly one mismatch. In the padded fixture the latter two test row padding and unused allocation tail separately. For a full allocation those positions coincide, which is recorded rather than represented as distinct locations.

Four invalid strides per module (zero, one below the required row size, 1281 and unsigned all-ones) must return zero and preserve every allocation byte after a valid render. Out-of-domain checker indices/mutations return unsigned all-ones. All 40 calls agree exactly between WasmKit and V8. There are 12 fault controls and 16 invalid-stride controls; baseline comparisons cover 819,200 whole-allocation bytes per interpreter and invalid-request comparisons cover 3,276,800 bytes per interpreter. The CLI exposes mismatch counts; the separately compiled checker performs each byte comparison internally.

The existing source controls still independently compare 614,400 native RGBA bytes and 614,432 literal/padding bytes, reject 15 unsupported source holdouts, and require exact normalized IR/standalone module repeats.

## Seals, tests and limits

Two successful seals are retained: initial interpreter control and final control after tightening checker geometry to reject heights beyond 160. New tests reject invalid checker domains, malformed geometry, Boolean numeric substitutions, oversize allocation and unsupported height. Existing tests retain typed-result corruption controls and source/controller flag validation; the full suite passes 223 tests.

Both interpreters ran on macOS. This is independent interpreter evidence for a tiny custom frontend and its saved renderer IR. It does not establish intended non-Apple/browser execution, general Swift/SwiftUI compatibility, source fixture compilation by Swift, live Canvas transport, hot reload or performance. F2 and both milestones remain open. The next portability gate is execution of an owned sealed module on an available intended non-Apple host, with independent byte expectations and host identity retained.
