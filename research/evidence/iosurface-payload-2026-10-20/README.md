# Surface payload geometry and same-ID changed-content control

Original IOSurfacePayload codec now requires surfaceID UInt32, scaleFactor CGFloat, width CGFloat, height CGFloat and selectableRegions. Unlike RenderPayload, it has no inferred default scale. The recovered receiver multiplies width and height by scaleFactor to construct pixel dimensions; region rectangles are wrapped unchanged in pixel space, with corner radius0. Prior reciprocal region-to-point geometry can then be applied separately. Decoder0x947dc/key getter0x945b0, independent five-case Swift reflection metadata and exact receiver FMUL/zero instructions establish this mapping. Strict Value Real types, bounds and errors remain original portable policy; Foundation coercion/null/error parity is not qualified.

A direct native call site identifies the selected consumer as DefaultMacOSPreviewArchiver.createStaticViewable. A LocalMacPlatformSupport flag selects layer-hosted versus IOSurface viewable; the flag's meaning is still unknown. This is scoped macOS static-path source evidence. It does not establish arbitrary Apple-platform/live-output compatibility, agent publication, command envelope or frame association. Addressable ModelPath parsing remains separate.

## New native resource/content experiment

The owned native oracle extends the prior receiver-copy control. After copying the first generation, it overwrites the same CPU-linear allocation under public lock/unlock, releases the creator's IOSurface reference while retaining the first receiver wrapper, then invokes the runtime-signature-verified initializer again with the same owned numeric ID. Both receiver surfaceID getters equal that ID. The second lookup succeeds in this retained-receiver condition and its complete128-byte copy is0x19; the first128-byte Data and image-provider snapshot remain unchanged. No unrelated surface ID is used. The numeric resource ID therefore does not imply unchanged contents in this owned CPU control. Local generation1/generation2 labels are experiment labels, not recovered native wire revisions.

All128 bytes of each copy are compared, including104 padding bytes. Baseline56 image output bytes also match, including32 padding/tail bytes. Source allocation tail stays excluded; ID0 returns nil. Three existing corruption controls still reject padding/tail/extent errors. A fresh bounded native replay passes. This demonstrates lookup/copy behavior with a retained receiver after creator reference release; it does not establish the sole remaining owner, final reclamation, kernel ID recycling, cross-process completion, GPU fences, no-later-effect or captured Canvas transport.

## Implementation verification

Sixty-one Rust tests pass (57 prior+4 new). Independent Python binary fixture checks the complete payload/region tree, Unicode/accessibility data and exact point-to-pixel projection. Controls cover all missing fields, UInt32 endpoints/overflow, strict scalar types, IEEE zero/infinite geometry and unchanged input. Frozen native/independent first and second byte generations feed the existing portable copy stage; the API never treats surface ID as a deduplication or revision key. The payload decoder performs no lookup or process action.

verify.py rechecks pinned hashes, reflection domain, native instruction constants and exact owned fixture bytes. replay.py builds original oracle.m using existing public SDK, checks the initializer's runtime method signature before NSInvocation and uses30-second compile/15-second execution bounds under the exclusive lock. The private Swift payload decoder/receiver are not called. Raw Apple decompilation and disassembly stay local; original reconstruction, owned fixtures and sanitized results are published.

```sh
python3 research/evidence/iosurface-payload-2026-10-20/verify.py
python3 research/evidence/iosurface-payload-2026-10-20/replay.py /private/tmp/FRESH-SURFACE-GENERATIONS
```

Prior evidence seal/members were verified; REA/analysis locks closed. No Xcode MCP/bridge, Xcode workspace/injection/restart, Apple signing/protection change or user-process termination occurred. No new failure was suppressed; predecessor compile failures remain sealed. R1/R2/native capture and both milestones remain open. Next recover agent-side surface publication/incremental capture, outer association and lifetime/completion boundaries, then correlate actual owned transport. Keep input dispatch and CrashListener cancellation as independent open tracks.
