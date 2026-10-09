# Storage and trace bridge delegation

Pinned FoundationHost SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`. Extends [State witness selection](2026-10-09-state-witness-pattern.md). No native Apple helper, private ABI, Xcode window or user process was invoked or modified.

## Prediction and static association

Competing explanations: selected payload destruction delegates through arbitrary generic functions, or fixed storage/trace witness bodies explicitly delegate reference words to bridge operations. Bounded acquisitions support the latter for these declared witness bodies. This does not prove the actual specialized State table selects them at runtime.

The generic `ObserverAndTokenStorage` descriptor's relative pattern field binds `0x135478`. Its independently predicted 16 pattern bytes point to instantiator `0xcb18`, null completion, flags `0x40000001` and witness table `0x1756d0`. Verified page-chain rebases bind its first three slots to `0x42900`, `0x4235c`, `0x42900`; predicted size/stride bytes are24/24. Reflection records name `observers` and `managedTokens`. Two reflected fields do not by themselves map the three reference words to field offsets.

For `InvalidationTrace`, the on-disk metadata address point `0x179338` has struct kind512. Verified rebases of its header table pointer `0x179330` and descriptor pointer `0x179340` bind table `0x1792d0` and nominal descriptor `0x1520e0`. The first three table slots bind `0xed44`, `0xdbc0`, `0xed44`; predicted size/stride bytes are8/8. Its reflection record names `links`. This static metadata association still establishes no observed runtime slide or live value.

## Complete delegation bodies

Storage destroy `0x4235c` saves the original value address, loads its reference words at offsets0/8/16 and delegates each to the declared Swift bridge-release import: two BL calls and one tail branch. Storage copy entry `0x42900` tail-branches through `0x42358` to merged helper `0x4238c`. That helper copies the first16 bytes through q0 and the last8 bytes separately; it delegates source words0/8/16 to the declared bridge-retain import in that order and returns the destination address.

Trace destroy `0xdbc0` loads its first word and tail-branches to bridge release. Trace copy entry `0xed44` tail-branches to `0xdb94`, which loads/stores one8-byte word, calls bridge retain and returns the destination. Complete bounded body identity and selected encoded load/store/register words are checked separately from direct branch targets.

The stubs, pointer-section indirect symbol indices, undefined external symbols and library ordinals independently bind `_swift_bridgeObjectRelease` and `_swift_bridgeObjectRetain` from `/usr/lib/swift/libswiftCore.dylib`. Actual dyld binding, runtime implementation, reference counts and deallocation remain unobserved.

## Verification and limits

Six sealed runs retained: three progressively expanded acquisitions, then three full controls. All192 selected body instruction bytes and24 import-stub bytes compare against independently mapped image bytes. Whole-body reviewed hashes are acquisition-derived identity checks, not independent semantic oracles. Pattern relative values and size/stride extents receive independent expected-byte comparisons; six witness slot rebases plus trace metadata header/descriptor rebases receive chain-membership checks. Reflection record kind/size/count and names are bounded and checked.

A separately labeled owned model covers130 combinations of one/three words, including null, repeated, high-bit and all-ones values. All3,040 copied fixture bytes compare to independent inputs. Delegation event sequences preserve duplicate/null arguments; three calls may address one allocation or no allocation. The model never performs actual Swift retains/releases and is not a native execution test. Six new tests cover alias multiplicity, unsigned/order preservation, every value byte, invalid operation/extent and malformed/missing/symbolic reflection names.A shared stub-verifier hardening additionally rejects missing/extra/duplicate instruction rows.204 tests pass.

Actual specialized runtime witness selection, retain/release effects, concrete allocation lifetime and physical reclamation remain open. So do live dictionary mutation, cancellation/completion races and correlated Canvas transport. Numeric State tags remain separate from source-case assignment. R1, R2 and milestone1 remain open.
