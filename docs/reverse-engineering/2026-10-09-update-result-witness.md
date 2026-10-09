# Separate waiting-state update result boundary

Pinned FoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`. Extends [State tag evidence](2026-10-09-state-case-tags.md) without assigning its case meanings to another enum. No private ABI calls or Xcode windows were used.

## Independent declaration and association

The nominal descriptor at `0x150928` independently names `WaitingStateUpdateResult` under `FulfillOnceState`. Its bounded field descriptor at `0x158154` has two enum records of 12 bytes, named `updated` and `alreadyFulfilled`. Their complete payload type strings compare with the separately acquired literal records `qd__\0` and `q_\0` (eight bytes). These strings are preserved without inferring concrete runtime generic types.

The complete 16-byte generic pattern at `0x134200` independently matches relative references to instantiator `0x30a18`, completer `0x2de9c` and table `0x173f88`. Four validated chained rebases associate destroy `0x2e054`, getter `0x2e860`, projector `0x1e5c` and injector `0x2e8f8`. The projector body was independently verified as a single RET in the prior State experiment; this experiment verifies its separate result table association.

No named result case-index constants were found in the bounded nlist search. Reflection order is not independent numeric case-index evidence. Accordingly `updated = 0` and `alreadyFulfilled = 1` remain unaccepted; the model uses numeric tags only.

## Complete body and numeric boundary

Corrected complete bodies comprise getter 152 bytes, injector 232 bytes, destroy 164 bytes and completer 136 bytes: 684 instruction bytes independently compared against mapped image bytes. Two declared import stubs add 24 independently compared instruction bytes, bound through Mach-O indirect symbols to Swift core metadata-state checking and multi-payload enum initialization. Acquisition-derived body hashes check identity, not independent semantic truth. Selected encoded loads, comparisons, condition selects, stores and direct branch targets receive separate checks.

For direct numeric tags 0/1, getter and injector derive offset `max(sizeA,sizeB)` from payload metadata at enum metadata offsets 24 and 32. Injector writes only that tag byte and branches to its epilogue. Destroy selects payload metadata offset 24 for numeric tag 1 and offset 32 for numeric tag 0, then tail-dispatches its value-witness destroy slot at offset 8. This is declared static delegation; it does not establish a concrete runtime object or release count.

Unlike State's size-derived trailer layout, this result projection adds no 57-byte trailer. For illustrative sizes 24/8 its tag offset is 24, while the separate State model yields 65. These illustrative sizes do not prove the instantiated result payload sizes. Tags above 1 follow extended paths, whose validity and behavior remain outside acceptance.

## Controls and retained limitations

The owned finite model checks 132,098 size/tag combinations for sizes 0..256 and tags 0/1. All 23,227,146 complete buffer bytes compare with an independent single-byte update oracle; payload and four trailing padding bytes remain unchanged. It also checks numeric destroy metadata selection. This is a hand-authored static projection, not execution of the Apple witnesses.

Three sealed runs are retained. Initial acquisition used an injector range that included the neighboring `FulfillmentOutcome` completer; no complete result-only claim is made for that range. Corrected acquisition narrowed injector to `0x2e8f8:0x2e9e0`. Its first verifier run rejected an incorrectly predicted pattern instantiator. Independent relative decoding recovered `0x30a18`; the corrected control passes. Four added tests check all non-tag bytes, unequal/zero sizes, the absence of a State trailer, invalid domains, missing tag bytes and corrupt branch conditions/opcodes/targets. The full suite passes 215 tests.

Native result construction, independently named numeric case association, concrete generic types and payload validity, actual witness dispatch, callback result selection, runtime cancellation/completion races and correlated Canvas transport remain open. R2 and milestone 1 stay open. Next work should prioritize a discriminating owned lifecycle or portable-subset gate while safe typed runtime observation remains unavailable.
