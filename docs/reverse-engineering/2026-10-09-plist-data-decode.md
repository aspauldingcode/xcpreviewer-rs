# Owned UVPropertyList data decoding and empty fallback

The prior [reply encoder](2026-10-09-transport-reply.md) has selected serialization-error paths constructing UVPropertyList from empty Data. A new bounded mode of the existing plist_corpus adapter executes the observed Objective-C initWithData/data/dictionary selectors in isolated owned helpers. It checks their runtime method encodings before invocation. No fabricated Swift ABI declarations or service contact are involved.

Native method image: PreviewsServices UUID `FFFB683F-5943-3C25-91B2-72D6E5174FA3`, macOS 26.5.1 (25F80), arm64, Xcode 26.6 (17F113). Both sealed native runs and prior transport anchors verify. [Sanitized cases and manifest anchors](../../research/evidence/plist-data-decode-2026-10-09.json) identify every owned input by size/hash.

## Measured boundary

| Input | UVPropertyList dictionary getter | Data getter | Independent Foundation parser |
| --- | --- | --- | --- |
| Valid empty binary dictionary | Empty dictionary | Exact original bytes | Empty dictionary |
| Valid identifier/unicode binary dictionary | Exact typed values | Exact original bytes | Same dictionary |
| Empty bytes; truncated trailer | Empty dictionary | Exact original bytes | Rejects |
| Bare bplist00; owned-invalid ASCII | Empty dictionary | Exact original bytes | Accepts legacy string roots |
| Valid binary array/string roots | Empty dictionary | Exact original bytes | Accepts corresponding root |

Each of eight inputs executes in two independent helpers. All records repeat exactly, all data comparisons cover every original byte, and both dictionary positive controls match independent Python values. Empty dictionary output alone cannot distinguish valid empty dictionary, rejected serialization or a non-dictionary root. Preserved data does not imply valid serialization.

## Retained harness failure

The initial run rejects its observations because Objective-C comparison expressions were boxed as integer NSNumber values rather than BOOLs; the verifier correctly refuses boolean/integer substitution. Its independent-decode assumption also incorrectly treated Foundation as a binary-only parser: Foundation accepts the two bare ASCII inputs as legacy string roots. The fixture unit tests independently catch a third issue, attempting to canonicalize absent None as a plist value.

The changed implementation casts presence flags to BOOL, treats absence outside typed plist values, and registers separate explicit Foundation legacy-string expectations. It then measures Foundation values, byte preservation and six empty-dictionary controls with a fresh sealed run. The failed run remains inconclusive; it is not reclassified as success. All 113 tests pass, including missing evidence, nonzero exit, corrupted data/value and boolean/integer substitution controls.

## Remaining scope

This is eight owned inputs at the Objective-C wrapper boundary. It does not force a LazyPropertyList serialization failure, execute a live reply callback, test Swift optional identifier absent/null/wrong-type behavior, cover arbitrary malformed data or observe attachments. It corroborates the consequence of the statically observed empty-data construction while leaving its runtime trigger open. No Xcode windows opened. P2/P1/R2 and both milestones remain open.
