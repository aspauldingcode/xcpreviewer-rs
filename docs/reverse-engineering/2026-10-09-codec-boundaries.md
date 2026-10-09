# Native codec key boundaries

Pinned target: Xcode 26.6 (17F113), arm64 PreviewsMessagingHost UUID `ce1040273729381b8f0cc774e404c0ce`, SHA-256 `0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c`. This extends the [IOSurfacePayload key checkpoint](2026-10-09-payload-keys.md).

## Findings

Nominal stored fields, nested enum cases and the strings returned by native codec key witnesses are distinct representations. Treating them as interchangeable would produce an incorrect decoder.

| Type/control | Stored fields | Returned key strings |
| --- | --- | --- |
| RenderPayload | bitmapDescription, selectableRegions, snapshotCornerRadius, scaleFactor | Same four strings |
| BitmapDescription | data, width, height, bytesPerRow, bitmapInfo, bitsPerComponent, bitsPerPixel, colorSpace | Same ordered list, with **byteOrder** inserted after bytesPerRow |
| ServiceMessage outer Key | identifier, content | **messageType, payload** |
| ServiceMessage PayloadKey | Same enclosing stored fields; singleton enum case named identifier | **__unique_service_message_identifier** |

The singleton identifier alias is a candidate path for investigating correlation. Its name alone does not establish how identifiers are generated, copied into replies, scoped, reused or consumed. Bitmap byte-order value semantics and its relation to bitmapInfo are likewise unresolved.

## Method and retained failures

The bounded adapter selects one pinned struct and its nested key enum independently. It disassembles exact key-witness symbols and interprets supported ARM64 instructions into Darwin immutable String literals. It reads the mapped image bytes for large literals, including the expected NUL terminator; unknown instructions, uninitialized registers, unsupported String representations, escaping control flow and instruction-budget exhaustion fail closed. There is no private Swift enum ABI call.

RenderPayload and outer ServiceMessage controls pass on the initial implementation. BitmapDescription initially fails on a different selector convention. Its observed two-instruction thunk loads w0 and branches to the exact rawValue getter. The revised adapter requires that exact thunk and interprets the bounded body using explicit w0 input, masking and signed b.le branching. Singleton PayloadKey initially fails because its getter has no selector load; explicit singleton constant entry then recovers the literal.

The original prediction that the identifier string equals its metadata case name fails on the revised harness. The controller conservatively records `inconclusive` for unmet checks; within the successful static extraction, this is a direct counterexample to name equality. That prediction is removed from the active campaign, while both original failed runs and the counterexample remain sealed. A separately registered alias control then passes. Predictions are not retroactively edited to manufacture success.

All seven native runs and frozen sources verify. All 109 tests pass using the existing research environment, including field/key separation, selector entry modes, signed comparison/branch behavior, absent flags and escaping/unknown control-flow rejection. An initial run using system Python lacked jsonschema and process-inspection permission; the complete existing-environment run passes without installing dependencies or changing protections.

[Sanitized contracts, observations and seven manifest anchors](../../research/evidence/codec-key-boundaries-2026-10-09.json) retain the exact outcomes. Raw Apple image and disassembly remain local. No Xcode workspace was opened.

## Remaining acceptance

These are static codec keys, not observed transport envelopes. No payload-value roundtrip, malformed-value acceptance, numeric transport IDs, reply matching, cancellation, resource completion or final release is established. R2, P1, P2 and both milestones remain open.

Next follow the identifier alias through exact ServiceMessage serializer/deserializer call sites, recover its value association, and obtain independent roundtrip/negative controls. The live capture gate still requires correlated request/reply and attachment observations; repeating static key extraction cannot close it.
