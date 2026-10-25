# Recursive override configuration values

Recovered PreviewOverridesConfiguration requires title:String first, then
SelectionBehavior, then ordered [PreviewVariant]. childVariantConfigurations
is an optional recursive Dictionary<PreviewVariant.ID,PreviewOverridesConfiguration>;
absence becomes empty, while present malformed data throws. Canonical output
always writes all four fields, including the empty child dictionary. Nested
variants and behavior reuse the sealed existing compatibility rules; unknown
fields are omitted and ordered duplicate variants remain intact. No default
selection aggregation, availability validation, selection or rendering occurs.

3,352 selected source bytes independently match LLVM across both pinned images.
Checks cover full parent raw key getter/encoder/decoder, required versus optional
calls/error branches, actual array/dictionary witnesses, empty-array storage
binding and dictionary-literal fallback, four-pair builder, shared dictionary
conversion and keyedMap. Conversions map all entries before constructing the
KeyValueMap; failures propagate. The generic map initializer assigns through
the subscript setter requirement, not a trapping unique-keys constructor.
Native private framework decoders are not invoked.

ChildConfigurations provides Unicode16 canonical lookup and dictionary equality
independent of key spelling, retains the first key spelling and replaces its
value on equivalent insertion. A public native Swift dictionary probe confirms
count1, last value and retained first spelling for the measured equivalent pair.
Existing String equality elsewhere remains unchanged. Children iterate in
portable normalized-key order; native dictionary iteration is not reproduced.

There is an explicit raw input-domain boundary. Two original binary plists each
contain canonically equivalent but byte-distinct keys in opposite wire orders.
Public Foundation parsing yields NSDictionary with2 keys, NSString equality is
false, while bridging to a Swift String-key dictionary yields1 key. Two complete
owned configuration-tree inputs using these keys are accepted/collapsed by the
original public Foundation composition, while reconstruction rejects both with
CanonicalKeyCollision on native Rust and actual WASI. This deliberate portable
restriction avoids guessing which native bridge value/spelling survives. It is
not native rejection parity, and does not prove the private framework's wire
route accepts these values. Typed Swift dictionaries cannot express both keys
simultaneously; ordinary typed-value controls are kept separate. Portable sibling
error indexes use raw-key order. Direct Value decoding caps configuration depth
at64; CLI binary plist structural/object limits apply independently. Ambiguous
bridge behavior and unbounded native depth remain outside parity.

The inspector adds explicit overrides-configuration mode. Bounded summaries show
root title, selection tag, total variants/children and at most four root variant
IDs plus four direct child IDs/titles, with individual escaping/256-scalar limits
and shown counts. Summaries do not recursively expand descendants. Canonical
output retains every complete supported descendant, normalized variant/behavior
and original key spelling. Full group/reply decoding remains pending.

All298 Rust tests pass, including four new complete expected tree/round-trip,
map equality/lookup/replacement, validation-order/nested-index/depth/ambiguity
and actual CLI/summary tests.28 original public Foundation compositions yield13
accepts and15 schema rejects. Actual WASI executes28 canonical cases plus13
summaries and2 documented ambiguity-policy rejects (43 invocations), without
filesystem preopens or inherited environment. Accepted ordinary canonical values
match complete type-sensitive expected dictionaries;13 WASI outputs pass public
Foundation reparse; accepted summaries match native Rust bytes. The2 boundary
inputs are separately accepted by the public native composition and rejected by
both portable implementations. boundary-policies.json preserves the distinction.
Disposable replay repeats source/four focused tests/all controls and boundary
probes. Full298-test output retained separately, restored after focused harness
replay. No implementation/test behavior failure occurred. One strengthened source
assertion expected a single-underscore storage import; exact Mach-O binding has
a double underscore. Expected binding corrected; excerpt inspection also needed
explicit __file__. Both tooling failures retained in source-initial-failure.txt.

REA package/path/catalog align; no target open or provider binding. Missing
private module and unsettled Ghidra inventory limitations remain in predecessor
evidence; no unchanged retry or guessed ABI. Raw Apple disassembly and symbol
inventory stay local ignored files. Only sanitized findings, original code and
owned control data are published. Complete group/reply semantics, ambiguous key
bridging, native dispatch/actions/Canvas interaction/refresh/rendering/provider
lifecycle and global resource settlement remain open. Both milestone contracts
remain incomplete.

Publication whitespace check caught one trailing space in the owned collision probe before commit. Whitespace removed, diagnostic retained; behavior unchanged. Unrelated staging restored byte-for-byte before retry.
