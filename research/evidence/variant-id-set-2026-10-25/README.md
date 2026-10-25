# Native set semantics and multi-select configuration

Recovered the shared Set property-list conformance in PreviewsFoundationHost:
encoding maps native Set iteration into an array without sorting. Decoding
maps and validates every array element, propagates an element failure, then
constructs a Set. MessagingHost MultiSelectConfiguration requires the
`defaultVariants` key with exactly Set<PreviewVariant.ID> conformance. Empty
arrays are valid, missing/malformed arrays reject, and all IDs must be String.
The full decoder/encoder/witness paths and actual bindings are checked against
1,308 independently matched LLVM source bytes across the two pinned images.

Public native Swift Set/String controls establish canonical Unicode equality,
case/compatibility distinctions, first input spelling retained for measured
duplicate cases, and process-varying iteration order (four process samples).
These controls use owned original Strings and public Swift/Foundation, not
private framework decoders. Actual Apple decoder invocation remains unproven.

Unicode version qualification found a real mismatch. The initially considered
unicode-normalization 0.1.26 uses Unicode18; 13,696 generated scalar canonical
decomposition/combining-order pairs produce21 native Swift equality mismatches,
all among combining-order cases. The retained unicode18-check.json records
every case; its generator/library version and raw generated-pair digest remain
local provenance. This version was rejected. unicode-normalization 0.1.24
(Unicode16) generates13,670 pairs:13,253 changed scalar decompositions and417
nonzero combining-class reorder pairs against U+0300. Every pair compares equal
under this public native Swift runtime. Full generated pairs are the checked-in
portable test fixture. Unicode16 is pinned in Cargo.toml; locked transitive
versions/checksums are in workspace Cargo.lock. This is finite, runtime-scoped
qualification, not proof for all possible Strings or future SDKs. Dependency
normalization implementation: https://docs.rs/unicode-normalization/0.1.24/unicode_normalization/ .
The public dependency is licensed MIT/Apache-2.0 with Unicode data licenses;
its own license files remain distributed by the registry package. Pair fixtures
are generated normalization outputs, not Apple code or binary extracts.

VariantIdSet stores canonical NFD keys separately from original spellings.
Insertion keeps the first representative, membership canonicalizes the query,
and set equality compares normalized keys independently of representative
spellings. Compatibility normalization and case folding are not used.
MultiSelectConfiguration decodes all IDs, collapses canonical duplicates and
emits the retained representatives. Portable output and summaries deliberately
use deterministic decomposed-key order; native randomized Set serialization
order is not reproduced. This documented output policy does not affect set
membership. Set equality is separate from String equality elsewhere in the
existing reconstruction, which was not broadened by this change.

The inspector adds explicit multi-selection mode. Summaries show at most eight
IDs, total/shown counts and individually escaped/truncated256-scalar strings.
Canonical binary output retains all unique complete representatives. There is
no membership validation against available variants, selection or application.
Full SelectionBehavior, PreviewOverridesConfiguration, groups and complete
variants replies remain pending.

All291 Rust tests pass, including four new complete-value/native fixture,
13,670 native-qualified equality/first-spelling pairs, missing/type/index and
actual CLI/bounded-summary tests. 25 original compositions with actual public
Swift Set/String and Foundation produce17 accepts/eight rejects. Actual WASI
executes25 canonical cases plus17 accepted summaries (42 invocations), no
filesystem preopens or inherited environment. Accepted output agrees with
complete type-sensitive dictionaries under the explicit portable ordering
policy;17 WASI outputs pass Foundation reparse; accepted native/WASI summaries
match bytes. Disposable replay regenerates and checks all13,670 pairs with
native Swift, verifies source, runs four focused tests and every Foundation/WASI
comparison. Full291-test output retained separately. A first checkout must
fetch the locked public dependencies before offline checks; no private modules
or Apple binaries are distributed.

Retained failures: initial dependency fetch lacked explicit RUSTC and exited
before download; corrected using the existing toolchain path. Unicode18 was
rejected after21 equality mismatches. The first Rust run failed two fixture
comparisons because the oracle used Swift's default String comparator rather
than the documented NFD-key ordering. Corrected only the oracle sort to compare
public Foundation decomposed UTF8 bytes; codec ordering stayed unchanged.
Initial stdout/stderr/fixture are retained with the corrected evidence.
No private Swift import or unsettled Ghidra inventory loop was retried. REA
package/path/catalog align; no target open, provider binding null.

Raw Apple disassembly and symbols remain local ignored files. The dependency
graph marks multi-select values and canonical ID sets as scoped implementations.
Complete override/grouped replies, native dispatch/actions, Canvas interaction,
selection/rendering/refresh/provider lifecycle and global resource settlement
remain open. Both milestone contracts remain incomplete.
