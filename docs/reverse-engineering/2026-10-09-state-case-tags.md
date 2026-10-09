# State case indices and direct tag boundary

Pinned FoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`. Extends [State pattern](2026-10-09-state-witness-pattern.md) and [storage/trace delegation](2026-10-09-storage-bridge-delegation.md). No live State value or Apple witness was invoked.

## Named index evidence

Two separately parsed nlist64 records define section symbols for the State `waiting` and `fulfilled` case-index constants at `0x1341d0` and `0x1341d4`. Symbol identity, uniqueness, defined-section type, section membership and address are checked independently of disassembler annotations. Their complete eight bytes compare to the independently predicted little-endian pair `(0,1)`. Bounded enum reflection records independently name `waiting` and `fulfilled` under the State nominal context.

The `WC` suffix denotes a resilient enum tag index in the [Swift mangling specification](https://github.com/swiftlang/swift/blob/main/docs/ABI/Mangling.rst). This corroborates the interpretation of the named constants; reflection order alone does not establish numeric ABI indices. This recovers a scoped static association of State waiting0/fulfilled1. It does not assign the same meaning to `WaitingStateUpdateResult`, cancellation selectors, wire message IDs or surface generations.

## Witness association and complete bodies

Three validated dyld page-chain rebases of State table slots at `0x173f70`, `0x173f78`, `0x173f80` bind getter `0x2dcf8`, destructive projector `0x1e5c` and injector `0x2dd9c`. Complete ranges comprise164,4 and256 instruction bytes respectively. The projector is a single RET; names shown by the disassembler may belong to another merged alias, so the table association and encoded word supply acceptance.

The getter derives the tag byte offset `max(sizeA, align8(sizeB)+57)` from payload metadata/table sizes. Its SUBS/B.LO path returns the original numeric tag byte directly for0/1. The injector's unsigned CMP/B.HI routes0/1 to the corresponding size calculation, writes w1 to that tag byte, then branches to its epilogue. Other tags take an extended path containing additional writes; this path is captured for identity but its semantics/validity are outside the accepted direct-tag model.

For the separately established on-disk storage24/trace8 size pair, the projection yields offset65. This aligns with the previously recovered specialized high byte at state offset65 and its numeric1 callback-suppression guard. Actual runtime table selection and actual instance sizes remain separate unknowns; no live race or callback execution is inferred from this alignment.

## Falsification and verification

Three sealed runs retained: initial bounded acquisition only, then two complete controls. All424 instruction bytes compare to independently mapped image bytes. Reviewed body fingerprints are acquisition-derived identity checks, not independent semantic oracles. Selected encoded load/store/return words, direct-tag conditional branch encodings and injector exit target receive separate acceptance checks. Case-index bytes, defined symbol records, reflected names and enum witness rebases are independently checked.

The owned finite model executes132,098 size/tag combinations for payload sizes0..256 and direct tags0/1. It compares28,088,564 complete buffer bytes with an independent expected tag offset and expected single-byte update. Four trailing padding bytes per buffer and all payload bytes remain unchanged. This model is not native Apple execution and does not establish enum payload validity. Seven added tests reject missing/duplicate/wrong-type/wrong-address/wrong-section symbols, unterminated names, missing tag bytes, extended tags, invalid size domains and changed payload/padding behavior.211 tests pass.

State's static case-index association is now recovered. Actual native getter/injector execution, runtime generic specialization, concrete payload validity, extended-tag behavior, `WaitingStateUpdateResult` source-case mapping, live cancellation/completion races and correlated Canvas resource cleanup remain open. R2 and milestone1 remain open.
