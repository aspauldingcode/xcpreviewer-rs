# Native IOSurface payload codec boundary

The pinned arm64 host image has an `IOSurfacePayload` value type with five nominal fields and a nested five-case PropertyListKey enum. A bounded ARM64 interpreter reads the actual native key-witness function; every selector's returned Swift String matches its independent reflection field name:

| Selector index | Key / field | Exported symbol type |
| --- | --- | --- |
| 0 | surfaceID | UInt32 |
| 1 | scaleFactor | CGFloat |
| 2 | width | CGFloat |
| 3 | height | CGFloat |
| 4 | selectableRegions | Array of SelectableRegion |

The serializer closure reads a 32-bit first value plus four 64-bit slots and builds a five-entry property-list dictionary using typed conformances. Public serializer and throwing deserializer entrypoints are separately selected and retained locally. This corroborates static codec structure; it does not execute payload serialization/deserialization or establish valid ranges.

No generation/completion/fence field is named within this bounded type. Such information may be carried elsewhere, including request/reply correlation or resource lifecycle state. Its absence here does not prove absence from the complete protocol. R2's native completion/cancellation rules remain open.

The first query matched five functions including closures but declared two, so its sealed result remains inconclusive. An exact public-entrypoint query then returns two and supports. The first key interpreter run fails closed at `cmp`; adding only the observed `cmp` and `csel` equality/signed-greater-than semantics yields all five strings. Tests cover 32-bit comparison, 64-bit signed overflow, missing flags, unsupported conditions, ambiguous descriptors, cycles and field drift. All 106 tests pass.

Image SHA-256 `0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c`, UUID `ce1040273729381b8f0cc774e404c0ce`. Type descriptor `0xd2248`, nested key descriptor `0xd22c8`, witness `0x945b0`. Selector indices are static enum-case indices, not transport IDs. No guessed Swift enum calling convention, service contact or Xcode window was used.

Raw binary/disassembly remains local. [Sanitized keys and four manifest anchors](../../research/evidence/surface-payload-keys-2026-10-09.json) retain both failures and successful dependent controls. Next: trace the surrounding RenderPayload/request/reply codec and identify where actual capture completion/resource reuse is represented; validate observed envelope and value roundtrips before portable decoder claims. R2/P1 and both milestones remain open.
