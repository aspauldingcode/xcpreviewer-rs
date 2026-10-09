# Token update value-witness dispatch

Pinned FoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`. This extends the [captured callback link](2026-10-09-token-callback-link.md) and [result consumer](2026-10-09-token-result-consumer.md). No native Apple function was invoked and no Xcode workspace was opened.

## Predictions and observations

Competing explanations: helper bodies directly select a reference-release routine, or dispatch through type-specific function pointers. The complete ranges `[0xebc8,0xec10)` and `[0x41dc,0x421c)` support the latter. Two initial sealed acquisitions establish body availability only; two subsequent controlled runs verify the complete bodies, resolver and runtime import. Controller `supports` labels on the initial runs do not establish the semantic hypothesis.

The copy helper saves incoming x1 as destination and x0 as source, passes x2/x3 to resolver `0x2710`, places the returned metadata in x2, loads the table pointer at metadata minus 8, loads slot plus 16 and calls through x8 with destination/source in x0/x1. It returns the saved destination. The destroy helper saves incoming x0, passes x1/x2 to the same resolver, places returned metadata in x1, loads table pointer at metadata minus 8, loads slot plus 8 and calls through x8 with the saved value in x0. It returns that saved address.

These slots and argument shapes agree with destroy and initialize-with-copy ordering in the upstream [Swift value-witness definition](https://github.com/swiftlang/swift/blob/main/include/swift/ABI/ValueWitness.def). This is source corroboration and a role inference, not a measurement of the pinned runtime's actual function pointers or their effects.

Resolver `[0x2710,0x2760)` saves the cache address, reads its word, tests bit zero and uses CMP/CCMP/B.eq to skip lookup for nonzero even words. Zero or odd words instead read a descriptor through incoming x1, extract its signed upper 32-bit length, add its signed lower 32-bit relative offset to the descriptor address, zero x2/x3, call stub `0x1313b4` and store the returned x0 through the saved cache address. Independent indirect-symbol indices for stub and pointer, undefined external nlist and library ordinal bind `_swift_getTypeByMangledNameInContext2` from `/usr/lib/swift/libswiftCore.dylib`. No runtime cache, descriptor contents or dyld binding was observed.

## Verification and limits

The controller captures exactly four bounded instruction ranges. All 216 helper/resolver instruction bytes, including stack frames and returns, match the independently mapped image and reviewed acceptance words; all 12 import-stub bytes are compared and its encoded addressing decoded separately. Three direct BL targets are decoded without trusting symbolic annotations. The cache gate projection agrees with an independent zero/parity oracle for 65,540 cases, including high-bit values. Mutation tests reject each of the 216 changed mapped bytes, each changed instruction with matching image bytes, missing/duplicate/extra entries and invalid gate controls. Import-linkage mutation coverage is shared with the separately tested stub verifier.

The verifier is a pinned finite static acceptance check, not a general emulator or proof of runtime ownership. Names and current upstream definitions alone cannot recover actual witness effects. Still required: selected metadata/cache and descriptor identities, concrete witness targets and payload ownership, native invocation/deallocation, cancellation races and correlated Canvas transport cleanup. R2 and milestone 1 remain open.
