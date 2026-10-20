# Nested crash-report reconstruction and remote envelope integration

The original portable core now models the recovered CrashReport, Image, Frame and Termination fields and connects report decoding/Value-tree serialization to agentCrashedDiagnostics and symbolicateCrashedDiagnostics. Together with the prior agentCrashed and requestScreenshot adapters, both recovered event cases and both request cases now have structural implementations. This is source-guided structural coverage, not private native decoder/transport parity.

## Independent source recovery

GhidraVibe recovered Image decoder0x3a354 (792 bytes), Frame decoder0x39d1c (788 bytes) and Foundation UUID adapter0x9fae8 (348 bytes); prior report/termination recovery and instructions remain pinned. Bounded ARM64/table inspection establishes the ten report key dispatch targets. Independent Swift reflection descriptors confirm every case name and exact domain: report0xd4380 has10 cases, Frame0xd4408 has6, Image0xd4460 has5 and Termination0xd44ac has8. These independently match valid case instructions and the image word table. The earlier broad decompiler switch inference is superseded within these confirmed domains; its spurious out-of-domain pseudo-cases are never used. Raw Apple code stays local.

schema.json records required/optional fields. Report ID is an optional UUID string with native generation when absent; time is a Date. Image uuid is a required arbitrary String, not a UUID parser input. Frame offsets/index and termination integers retain pinned-host signed64-bit semantics. Optional empty strings, arrays and dictionaries remain distinct from absence; no extra geometric/process validity rules are invented.

## UUID and default boundary

The source UUID adapter delegates to Foundation.UUID(uuidString:). An original public Foundation oracle independently checks10 input/canonical-output cases, including mixed case, compact/braced/space-padded/invalid/Unicode strings and zero UUID. The Rust parser matches all outcomes and canonical uppercase strings. Four additional public native UUID() samples have version4/RFC4122 variant bits; uniqueness/format checks are measured observations, not entropy-strength qualification or deterministic output equivalence.

For absent report IDs, decode_with_entropy takes an explicit fallible caller entropy function, calls it once only when needed, and sets version4/variant bits. Modern reports with IDs require no entropy source. The convenience decode method returns EntropyRequired on absent IDs; it does not silently choose an Apple-specific service or fixed UUID. This portable host boundary and error are original API policy, not an identical Foundation error. Host entropy integration/quality remains a separate runtime requirement. Tests verify laziness, exact masking, error propagation and ID generation before later required-field validation, matching the recovered ordering.

## Verification and usable tools

Forty-seven Rust tests pass (39 prior plus8 new suites). Five independently serialized original Python plistlib fixtures cover full/minimal reports, canonical UUID serialization and both report-bearing envelopes. Tests compare the complete decoded-value trees, nested metadata and optional emptiness; exercise required/nested type errors, signed ranges and missing-ID behavior; preserve inputs; and cover all four recovered event/request cases. Narrow legacy notification/screenshot helper APIs remain available and reject report variants they cannot represent; the new full RemoteEventPayload and RemoteEventRequest APIs carry reports.

inspect-preview-crash now handles both notification and report events. inspect-preview-request inspects screenshot or report-symbolication requests. Neither sends a request or operates on a PID.

```sh
cargo run --offline -p canvas-core --bin inspect-preview-crash -- tools/re/rust/canvas-core/tests/fixtures/crash-report-model/event-report.bplist
cargo run --offline -p canvas-core --bin inspect-preview-request -- tools/re/rust/canvas-core/tests/fixtures/crash-report-model/request-report.bplist
```

Both report examples produce canonical ID00112233-4455-6677-8899-AABBCCDDEEFF, pid12345 and one image/frame. Existing notification CLI output is retained. A fresh read-only replay verifies key metadata against the pinned artifact, rebuilds/runs public UUID oracles, reproduces all five fixture bytes, runs tests/builds and checks both report CLIs. replay.log records success. The failed first Swift compile's module-cache restriction is retained; an explicit temporary cache corrected it without changing permissions or protections.

## Limits and next work

Only UUID behavior here is compared with a public native runtime; nested report compatibility is established from source and independent owned fixtures. No private CrashReport/transport method was called. Foundation coercions, explicit-null treatment, exact native error payloads, arbitrary malformed-input parity and captured native reference reports remain unqualified. The serializer returns Value trees, not binary plist bytes. The selected two framework trees expose no typed Swift modules/interfaces at the inspected locations; that bounded inventory does not establish global absence. Do not invent private Swift ABI declarations.

The prior date/request evidence seal was fully reverified. Framework/REA/Ghidra identities, raw provenance and all failures are retained. Native operations were bounded and serial under the exclusive controller lock; REA and acquisition lock were released. No Xcode MCP/bridge, system-protection change, Apple re-signing, user workspace/process termination, live injection or unchanged Frida retry occurred.

Next move from completed data-model work to actual failure consumers and transport/resource effects. Identify safe owned observation/injection routes where existing permissions allow, correlate native lifecycle messages and cleanup, and locate actual view-input forwarding independently. Do not repeat unchanged geometry/date/UUID controls as progress. A crash report is not a release/no-later-effect receipt. R1/R2, private native capture and both milestones remain open.
