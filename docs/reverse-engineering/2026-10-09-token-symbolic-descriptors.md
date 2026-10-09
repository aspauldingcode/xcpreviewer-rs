# Token state symbolic descriptor association

FoundationHost pinned SHA-256 `1558308e07d07693414f8681269d2e7d79226a4b3fa7aacf976bcdf60b0b5c4d`, UUID `6b75229bde5d3d3794bc75af4f4704c6`. This extends [value-witness dispatch](2026-10-09-token-value-witness.md), without executing Apple helpers or opening Xcode windows.

## Discriminating prediction

The two update wrappers could pass a generic, shared type descriptor or distinct specialized storage-state records. Encoded ADRP/ADD pairs and BL targets support distinct records associated with the shared update body. Initial local acceptance expected the first reference to name `FulfillOnceState`; inspection falsified that literal expectation: it names the nested enum `State`, whose independently followed parent is `FulfillOnceState` in `PreviewsFoundationHost`. The retained preflight diagnostic is not a controller seal. Corrected acceptance checks the complete parent path.

| Wrapper | On-disk cache | Descriptor | Length-delimited type record | Distinct nominal references |
| --- | --- | --- | --- | --- |
| `0xbeea8` | `0x187be8` | `0x13c080` | `0x148ec0`, 30 bytes | ConcurrentInvalidationObserverBox, ConcurrentTokenCallback |
| `0xbeecc` | `0x187c00` | `0x134478` | `0x148f00`, 30 bytes | IsolatedInvalidationObserverBox, IsolatedTokenCallback |

Both records also reference `PreviewsFoundationHost.FulfillOnceState.State`, `ObserverAndTokenStorage` and `InvalidationTrace`; the remaining operator characters are `yyG_G`. The nominal associations are resolved, while a complete demangling and runtime specialization remain separate. Both eight-byte cache words are zero on disk; this establishes no runtime cache value.

Each record contains five indirect symbolic references. Relative offsets may contain NUL bytes, so splitting at the first NUL loses the record. The new bounded reader uses the descriptor's signed relative pointer and explicit length, skips four-byte symbolic operands, checks the terminating byte and follows only supported direct/indirect nominal references. [Swift's symbolic mangling specification](https://github.com/swiftlang/swift/blob/main/docs/ABI/Mangling.rst#symbolic-references) corroborates these widths and embedded-NUL behavior.

An indirect slot contains a chained rebase word rather than a normal address. The new read-only resolver validates the load command, payload bounds, segment identity, page-start table and actual membership reached by traversing the chain. Only untagged, non-bind `DYLD_CHAINED_PTR_64_OFFSET` is supported; unsupported pointer formats, tagged/bind targets, reserved bits, absent/multiple starts, out-of-page traversal and nonmembers fail closed. [Apple's fixup-chain definitions](https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/fixup-chains.h) corroborate the format and four-byte stride. This is static address resolution, not actual dyld execution or binding.

## Verification and remaining scope

Three accepted controller runs seal the acquisition and verifier source. All 72 wrapper instruction bytes are independently mapped and compared. Encoded pointer pairs and direct branch targets are decoded separately; descriptor extents, 62 record/terminator bytes, ten symbolic references and 16 zero cache bytes are checked. Record span checks establish bounded parsed identity, not a claim that every record byte has an independently predicted golden value. Nine added tests cover owned wrapper identity, each changed wrapper byte, changed cache/descriptor/reference/terminator values, chain nonmembers, broken links, unsupported/bind/reserved/tagged pointers, truncation and embedded NUL behavior.

Actual resolved metadata, generic instantiation, concrete witness target addresses/effects, payload reference counts, live dictionary contents, cancellation races and correlated Canvas transport remain unknown. R2 and milestone 1 remain open.
