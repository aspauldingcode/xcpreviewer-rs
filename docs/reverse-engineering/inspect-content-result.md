# Inspect variant entries and selected overrides

```sh
cargo run --offline --manifest-path tools/re/rust/canvas-core/Cargo.toml \
  --bin inspect-content-result -- variant variant.bplist
cargo run --offline --manifest-path tools/re/rust/canvas-core/Cargo.toml \
  --bin inspect-content-result -- --canonical override selected.bplist > normalized.bplist
cat variant.bplist | cargo run --offline \
  --manifest-path tools/re/rust/canvas-core/Cargo.toml \
  --bin inspect-content-result -- --canonical variant - > normalized.bplist
```

Additional modes: `configuration` decodes PreviewVariantsConfiguration with a required title and required ordered sections array; `section` decodes an optional title and required ordered variants array. Empty arrays are accepted; missing arrays reject. Nested variants use the same compatibility rules below. Configuration summaries show at most four sections and four entries per shown section, with counts; canonical output retains everything. These modes do not decode whole groups, override selection configuration or apply a selection.

Select the expected kind explicitly: `variant` means one PreviewVariant entry;
`override` means ContentOverridePayload, an optional selected override string.
This command does not infer the kind, match a request, inspect a whole grouped
reply, or apply an effect or override. Use inspect-service-message for requests.

Variant decoding checks renderEffects first. If that key is absent, a valid
legacy renderEffect dictionary is required. A present empty array wins over any
legacy value; a present malformed array fails without retry. Each effect has a
required opaque String id. Variant id and displayName are required strings.
Optional interfaceOrientationOverride accepts portrait, portraitUpsideDown,
landscapeLeft or landscapeRight; absence remains absent, with no portrait
default. Canonical output writes the full modern array and a legacy first effect.
For an empty array, the legacy dictionary contains id="Missing", matching the
recovered compatibility encoder; this placeholder is not an applied effect.

Override decoding accepts an absent contentOverride and preserves an explicit
empty string. A present non-string fails. Unknown fields are omitted during
canonical encoding. An unrelated dictionary can therefore decode as an absent
override; the caller must select the correct expected result kind. No evidence
of request matching, successful application or peer liveness follows from it.

Default output shows escaped strings, at most 256 Unicode scalars per string,
with original UTF-8 byte counts and truncation flags. At most eight effect IDs
are shown, with total/displayed counts. `--canonical` emits only normalized
bplist00 bytes to stdout; diagnostics use stderr and failure is nonzero. Input
is limited to 64 MiB and existing plist object/depth/output limits apply. Check
exit status before consuming output; a write failure may leave partial stdout.

The same command runs under actual WASI preview1. Standard input needs no
filesystem preopens; named input needs a host-granted directory. Verification
uses explicit standard-I/O handles, no preopens and no inherited environment.
Browser execution, private decoder/runtime parity, transport correlation, ambiguous key bridging, and
actual rendering/lifecycle/resource settlement remain outside this result.

## Single-select configuration

Use `inspect-content-result single-selection INPUT.bplist` (or `-` for stdin) to inspect an individual SingleSelectConfiguration. Add `--canonical` before the kind to emit normalized binary plist stdout. Both `style` and `defaultVariant` are required strings. Style must be `list` or `range`; defaultVariant is an opaque ID, including empty or unknown strings. Style errors precede default-ID errors. Unknown dictionary fields are omitted from canonical output. Summaries escape IDs, cap them at 256 Unicode scalars and report original byte length/truncation; canonical output preserves the complete ID.

This mode does not choose or apply a variant, check membership in another configuration, decode full override configurations or decode grouped replies. Multi-select values are now available through the separate mode below.

## Multi-select configuration

`inspect-content-result [--canonical] multi-selection INPUT.bplist|-` decodes the required defaultVariants array of opaque String IDs. Empty arrays are valid. Missing or malformed arrays and non-String elements reject; failures retain the offending array index. Canonically equivalent Unicode IDs collapse, retaining the first input spelling. Case and compatibility forms remain distinct. The public VariantIdSet API uses the same equality for insertion, membership and set comparison, preserving original spellings. This does not validate membership in another configuration or choose/apply variants.

Native Set serialization order varies between processes. Portable canonical output and summaries instead use deterministic decomposed-key order; this is a documented ordering policy, not byte-identical native Set serialization. Summaries show at most eight default IDs, total/shown counts and per-ID escaping/256-scalar limits. Canonical output retains every unique complete ID. Grouped payloads are available through variants-reply below.

The pinned normalization dependency is unicode-normalization 0.1.24 (Unicode 16), with transitive versions/checksums in the workspace Cargo.lock. Unicode 18 produced21 combining-mark equality mismatches against this native Swift runtime; Unicode 16 passed13,670 generated scalar-decomposition/reordering pairs. Those controls qualify the measured runtime, not every possible String or future SDK. The crate implements Unicode canonical normalization ([documentation](https://docs.rs/unicode-normalization/0.1.24/unicode_normalization/)); compatibility normalization and case folding are not used. A first checkout must fetch the locked public dependencies before offline builds.

## Selection behavior

`inspect-content-result [--canonical] selection-behavior INPUT.bplist|-` decodes the required `discriminant` String (`singleSelect` or `multiSelect`), then requires only the corresponding `singleSelectConfiguration` or `multiSelectConfiguration` payload. Inactive payloads are ignored, including malformed ones. Active payload errors propagate with their existing portable cause; no alternate branch is tried. Unknown/wrong-case discriminants reject even with valid payloads. Canonical output contains only the discriminator and active normalized payload.

Summary output reports the active discriminator and its single default ID/style or bounded multi-default set, using the same escaping/limits and deterministic set-order policy as the individual modes. This value codec does not apply a selection or check its validity against available variants. The parent overrides-configuration mode below handles recursive child values with an explicit raw-key ambiguity boundary. Grouped payloads are available through variants-reply below.

## Override configuration tree

`inspect-content-result [--canonical] overrides-configuration INPUT.bplist|-` requires title:String, selectionBehavior and an ordered variants array, in that validation order. Optional childVariantConfigurations is a recursive dictionary of variant ID to override configuration; absence becomes empty. Present malformed children reject. Canonical output always writes all four fields, including the empty dictionary, recursively normalizing existing variants and selection payloads. Summaries show root title/tag/counts and at most four root variant IDs and four direct child IDs/titles, with escaping/counts; deeper values remain in complete canonical output. No selection, default-selection aggregation, membership validation or rendering is performed.

ChildConfigurations provides Unicode16 canonical ID lookup, retains the first key spelling and replaces the value on repeated equivalent insertion. Raw Value input with two canonically equivalent child keys is explicitly rejected as CanonicalKeyCollision: Foundation can preserve both NSDictionary keys, but bridging to Swift String-key dictionaries collapses them. That ambiguous wire/bridge behavior is not reproduced; this is a portable input-domain restriction, not native rejection parity. Sibling error indexes follow portable raw-key order, not native dictionary enumeration. Direct Value decoding caps recursive configuration depth at64; CLI binary-plist object/depth limits still apply. Ambiguous key bridging, transport correlation and private/native Canvas/resource parity remain open.

## Groups and variants payload

Use `inspect-content-result [--canonical] group INPUT.bplist|-` for a PreviewVariantGroup, or `variants-reply` for a PreviewVariantsPayload. The latter is the value payload only: it does not decode a transport reply envelope, correlate a request, establish reply success or apply/render its contents. Request payloads remain in inspect-service-message.

A group requires an opaque String id, then reads optional associatedGroupIDsArray (absent becomes empty), optional overridesConfiguration and optional variantsConfiguration. Present malformed optional values reject; nested errors propagate. Associations use Unicode16 canonical set equality, retain first spelling and serialize in deterministic NFD-key order. Self/unresolved links are retained without graph resolution. The similarly named associatedGroupIDs key is not the wire key and is ignored. Canonical group output always includes the association array, omitting absent configurations. Nested recursive override restrictions, including CanonicalKeyCollision and depth bounds, remain in force.

The payload requires an ordered groups array; empty is valid, missing rejects, and duplicate groups/IDs remain intact. A bad group rejects the whole value with its index/cause. Canonical output retains every complete supported group and configuration. Summaries show at most four groups, four association IDs per shown group, optional configuration titles, total/shown counts and the usual individually escaped256-scalar strings. Summaries do not expand configuration trees. Native set byte order, ambiguous key bridging and end-to-end reply/rendering/resource behavior remain outside parity.

## Calculate default selection

`inspect-content-result [--canonical] default-selection INPUT.bplist|-` decodes an override configuration, then calculates its default ID set. A single-select node starts with its one default ID; a multi-select node starts with its configured set. Only child configurations whose keys match those initial IDs contribute recursively. Newly contributed IDs do not activate sibling children. Missing IDs and self-looking references are kept; variants-array membership is not validated and children are owned trees, not graph references. Empty initial multi-defaults visit no children.

The library method `PreviewOverridesConfiguration::default_selection()` returns an owned VariantIdSet without modifying configuration state. Parent representatives survive equivalent child IDs. Portable sibling traversal follows deterministic ID order; native Set traversal is unordered, so a spelling shared by two contributing children can differ natively even when membership agrees. This remains an explicit representation-policy difference.

Summary output shows at most eight selected IDs with counts and existing escape/length limits. Canonical output is the complete calculated String array in portable order, a derived result format rather than an Apple transport payload. Parsing still validates every configuration child, including unselected children, and retains existing ambiguous-key/depth boundaries. Calculation does not apply overrides, render, call native selection methods or prove native getter/transport/resource parity.

`group-variants` decodes a complete group and enumerates its variants. `overrides_variants()` returns only the direct override configuration variants; children are excluded. `grid_variants()` flattens sections in order, preserving duplicates. `all_variants()` visits override variants then grid variants, retaining the first equal full value. Canonical Unicode 16 equality applies to IDs, display names and each ordered effect ID; optional orientation is significant. The public model's derived `PartialEq` continues to compare stored spellings; the enumeration's internal membership key has the qualified Swift String semantics. No selection filter, association resolution or effect application occurs.

The summary displays up to eight IDs/names per list, escaped and limited to 256 scalars per String. `--canonical group-variants INPUT` emits a complete derived dictionary containing `overrides`, `grid` and `all` variant arrays. This dictionary is an inspector result format, not an Apple wire payload. Missing configurations yield empty lists; malformed present configurations (including excluded child configurations) still fail complete group decoding.

`render-effects` assembles effects from already resolved variants: every override's ordered effects, then the optional configuration variant's effects. Duplicates and original spellings survive; names, variant IDs and orientation do not add effects. This does not select override IDs, calculate defaults, resolve content overrides or execute updates.

Its input is an **original inspector format**: a dictionary with required `overrides` (an array of variant dictionaries) and optional `variant` (a variant dictionary). It is not an Apple wire payload. Existing variant decoding, including modern/legacy effect fallback and malformed-present rejection, applies to each entry. Unknown tool fields are ignored. The summary shows up to eight escaped256-scalar effect IDs with total/shown counts. `--canonical render-effects INPUT` emits the complete derived array of RenderEffect dictionaries. Library callers can use `render_effects::assemble(&overrides, variant.as_ref())` directly.
