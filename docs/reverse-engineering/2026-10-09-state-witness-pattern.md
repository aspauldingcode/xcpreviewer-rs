# Generic State witness pattern

Pinned FoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`. Extends [resolved token type records](2026-10-09-token-symbolic-descriptors.md). All work is read-only static analysis and finite projection; no Apple helper or runtime metadata accessor was invoked.

## Pattern association

The enum descriptor `0x1508f8` has the State parent path, flags `0xd2`, two payload cases, zero empty cases, and the reviewed generic header. Its relative fields point to accessor `0x2cfc8`, instantiation cache `0x1878c0` and default pattern `0x1341c0`. The pattern's independently predicted 16 bytes bind instantiator `0xec10`, completer `0x2d148`, flags `0x40200000` and value-witness pattern table `0x173f18`. These layouts are corroborated by [Swift's metadata definitions](https://github.com/swiftlang/swift/blob/main/include/swift/ABI/Metadata.h); this corroboration is not proof of actual runtime specialization or table selection.

All eight on-disk table pointers are independently resolved through verified dyld format6 page-chain membership. Their declared targets are `0x2d1e4`, `0x2d360`, `0x2d410`, `0x2d544`, `0x2d720`, `0x2d854`, `0x2da30`, `0x2db44`. The destroy and initialize-with-copy pattern slots select `0x2d360` and `0x2d410`; the other six bodies are not accepted as recovered semantics here. This is the generic pattern, not an observation of the specialized token state's runtime table.

Initial acquisition covered `[0xec10,0xec48)`; inspection found the instantiator ends in a tail branch at `0xec14`, and the remainder belongs to another helper. Final acceptance narrows this range to `[0xec10,0xec18)`. The initial seal proves acquisition only, not semantics of a 56-byte instantiator.

## Recovered bounded bodies

The instantiator sets w3 to24 and tail-branches to the declared Swift generic-value allocation import. The completer requests metadata checks with w0=319 for the metadata at offsets16/24. Responses greater than63 take the dependency return path. Otherwise it obtains tuple layout and invokes multi-payload enum initialization with w2=2. Four independently decoded import stub/pointer tables and library ordinals bind `_swift_allocateGenericValueMetadata`, `_swift_checkMetadataState`, `_swift_getTupleTypeLayout2` and `_swift_initEnumMetadataMultiPayload` to Swift core. Actual execution, responses and allocation effects remain unobserved.

The destroy body reads the two payload metadata pointers at offsets16/24, reads both table size fields at offset64, and computes `max(sizeA, align8(sizeB)+57)` for the tag byte offset. For direct numeric tags0/1, its final conditional selects payload metadata/table A/B respectively, then tail-dispatches through that table's destroy slot8. Extended-tag decoding exists in the complete captured body but is outside the accepted finite projection.

The copy body computes the same tag offset. Direct tag1 calls the B copy slot16 and copies a trailing57-byte region after an aligned B payload; direct tag0 calls the A copy slot16. The tag1 trailing vector writes cover offsets `[41,57)`, `[16,48)` and `[0,16)` with seven overlapping bytes; their union covers all57 bytes with no gap. It finally writes numeric tag1/0 to the destination. The independent projection covers layout sizes0..256 and both direct tags (132,098 cases); a separate full57-byte pattern comparison covers the overlapping trailing copy. These are static projections, not native calls, retain-count checks or a proof for every possible runtime value. Numeric tags are not assigned source enum names by this verifier.

## Evidence strength and remaining gaps

Final runs compare all648 bounded body instruction bytes and48 import-stub bytes against independently mapped image bytes. Whole-body reviewed hashes check identity; they are derived from the inspected acquisition and are not independent semantic predictions. Encoded direct call/tail targets, pattern relative values, fixup membership and runtime import tables receive separate checks. Seven added tests cover each changed owned-body byte, matching-image body changes, missing/duplicate/extra instructions, unmapped reads, alignment/tag boundaries, every trailer byte, and truncated/oversized trailer inputs.

Three seals are retained: first acquisition only, then two complete controls.197 tests pass. Runtime metadata creation/completion, specialized witness table selection, payload-specific witness effects, retain/release accounting, races and correlated Canvas transport remain unknown. R2 and milestone1 remain open. No Xcode windows or user processes were touched.
