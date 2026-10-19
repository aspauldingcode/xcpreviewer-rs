# Remote preview crash-notification reconstruction

The proposed RemoteEventPayload view-input route was falsified. Direct GhidraVibe recovery and independent ARM64 checks show that Ultraviolet.PreviewRemoteEvents carries agent crash/diagnostics notifications, with discriminants agentCrashed and agentCrashedDiagnostics. It is not evidence of mouse/touch/key dispatch. CanvasControlEvent remains a separate control path. This correction supersedes the earlier geometry checkpoint's suggestion to investigate this stream as view input.

## Recovered source behavior

The pinned current ARM64 PreviewsMessagingHost SHA-256 is0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c. REA6.2.0 target/server identity was checked; GhidraVibe0.1.1/GhidraMCP5.14.2 decompiled focused functions under the exclusive controller lock. Raw pseudocode/instructions stay local. Source recovery includes decoder0xafd2c (716 bytes), serializer0xaf9c0 (692 bytes), key getter0xaf90c, discriminant getters and stream getter0xae744. Long Swift string pointers were resolved with their actual literal bias; byte addresses and sanitized strings are recorded in findings.json. The previous geometry seal and its source blobs at e9c2a168ee249b0ad4bf37faf8ee1528f2f2f171 were reverified.

The agentCrashed branch contains a required Int32 pid and diagnostics behavior. Native decoding first attempts optional agentBehavior, whose nested discriminant is willProvide, canSymbolicate or unavailable. Only when that field is absent does it read the required legacy diagnosticsComing Bool: true becomes willProvide, false becomes unavailable. A present malformed/unknown modern field throws rather than falling back; ARM64 Swift error-register checks confirm this where decompiler pseudocode omits branches. PID decoding follows behavior decoding. A present valid modern field bypasses the legacy field, including malformed or contradictory legacy values.

Serialization writes the modern nested agentBehavior and the legacy diagnosticsComing Bool. The compatibility Bool is true only for willProvide; canSymbolicate and unavailable both project to false. Thus an old reader loses the modern canSymbolicate distinction. The separate agentCrashedDiagnostics branch carries a PreviewsFoundationHost.CrashReport, whose nested schema has not been reconstructed here. The codec explicitly rejects that variant instead of accepting an unvalidated opaque report.

## Original implementation and independent checks

The original Rust remote_crash module provides AgentCrashNotification decoding from typed or binary property-list values, DiagnosticsBehavior, a decoded-value-tree serializer and the exact stream identifier. inspect-preview-crash reads a bounded binary plist and prints supported notification metadata. It never acts on the PID or sends a transport message. A notification alone does not establish process identity, resource release, receiver-first cleanup, operation settlement or absence of later effects.

Five original independent Python plistlib fixtures cover all3 modern behaviors and both legacy Bool values. Thirty-five Rust tests pass (30 prior plus5 new suites): modern/legacy decoding, exact serializer-tree comparison, malformed legacy bypass, malformed modern rejection, required fallback/error order, Int32 boundaries, unknown discriminants and explicit unreconstructed-variant rejection. Five CLI fixture checks and an unrelated-payload rejection pass. replay.py independently reproduces every fixture byte/hash, runs tests in a fresh temporary target directory and checks all5 CLI results without source mutation. replay.log retains that verification.

These tests validate the source-recovered reconstruction and original strict typed-value policy, not a private native decoder invocation or captured wire corpus. Foundation numeric coercions, explicit-null optional treatment, native error payloads and complete malformed-input parity remain unqualified. The serializer emits a Value tree; a binary serializer and transport send path are not implemented here. Negative/zero Int32 PIDs are accepted as data without inventing process validity rules.

```sh
cargo run --offline -p canvas-core --bin inspect-preview-crash -- tools/re/rust/canvas-core/tests/fixtures/remote-crash/modern-canSymbolicate.bplist
```

Expected output includes stream=Ultraviolet.PreviewRemoteEvents pid=12345 agent_behavior=CanSymbolicate.

## Remaining frontier

Recover CrashReport fields and the RemoteEventRequestPayload subscription/request semantics (decoder0xaef7c, serializer0xaebd8), then trace the actual failure/diagnostics consumer and resource effects. Investigate actual input forwarding separately in the developer/UI/simulator integration rather than assuming an event-named stream is input. Both milestones and native R1/R2 acceptance remain open. No Xcode built-in MCP/bridge, private Swift ABI call, live attachment/UI/workspace operation, protection change or unchanged failed Frida retry was used. Bounded acquisitions completed, REA closed and the analysis lock was released.
