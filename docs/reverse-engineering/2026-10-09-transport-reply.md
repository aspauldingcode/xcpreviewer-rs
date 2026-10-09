# Static transport reply callback and encoding boundary

Pinned Xcode 26.6 (17F113), macOS 26.5.1 (25F80), arm64 messaging image SHA-256 `0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c`. Prior optional identifier anchors verify before reuse. Two new bounded exact-symbol probes select the encodedReplyHandler initializer and two primary closures, then the success callback's LazyPropertyList encoder. [Sanitized sites and two manifest anchors](../../research/evidence/transport-reply-path-2026-10-09.json) verify frozen sources and raw artifacts.

## Callback path

TransportReply.init(encodedReplyHandler:for:) captures the supplied callback pair in a closure context and constructs a PreviewsFoundationHost Continuation with a resume closure and failure mode. The input UVPropertyList is captured separately for diagnostic initialization information. This is evidence of callback routing, not proof of exactly-once completion.

The result-handling closure selects success or failure by the Result tag. Failure converts the Swift error through HumanReadableError.serializableNSError, then invokes the captured callback with null payload and that error. Success obtains LazyPropertyList.encoded, then invokes the callback with encoded payload and null error. No explicit ServiceMessage identifier copy occurs in this selected result-handling closure. Identifier propagation may occur in its inputs, other layers or caller closures; the whole protocol remains unobserved.

## Encoder boundary

LazyPropertyList.encoded checks OS version with arguments 14,4,0. The newer branch calls its data getter and constructs UVPropertyList via initWithData; the other branch obtains a serializable dictionary and constructs via initWithDictionary. Selected serialization-error paths log and fall back to empty Data or empty dictionary construction. Consequently the outer success callback's null error argument alone cannot establish successful payload serialization.

These are static branch/call-site findings. They do not measure behavior on older OS versions, force a serialization failure, execute callbacks, establish empty-data acceptance or prove actual live reply contents. Function-count checks validate selection only; call-site interpretation is separately scoped analyst analysis. Existing 110-test implementation checkpoint is unchanged, and added campaign entries validate. Raw disassembly remains local; no Xcode windows opened.

Next add safe owned UVPropertyList empty/malformed/valid-data decoding controls to investigate the observed fallback boundary. Follow the Continuation resume guard independently for completion semantics. Live correlated envelopes and attachment observations remain required; P1/P2, R2 and both milestones stay open.
