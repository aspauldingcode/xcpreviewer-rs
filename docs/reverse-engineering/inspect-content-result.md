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

`effective-overrides` resolves already stored group settings. A group needs matching enabled settings and an override configuration. Grid mode excludes its associated group's canonical ID. Direct variants are filtered in order by the settings selection set; selected direct variants activate only their matching immediate child configurations. Selected child variants append after all selected direct variants. A fixed direct-result snapshot prevents cascading into siblings or grandchildren. Duplicate groups, variants and child expansions survive. Missing/disabled settings skip the group; an enabled group with no selected variants remains as an empty override list. Defaults, selection style and associatedGroupIDs are not consulted.

This mode uses an **original inspector input format**: required `groups` (group wire-value array) and `settings` (ordered array of dictionaries with required `groupID` String, `isEnabled` strict Bool and `selection` String array). Optional `gridGroupID` String projects CanvasMode.grid's associated group ID; absence projects live/static. Sequential settings assignment uses canonical IDs and last value wins. The tool validates every input before resolution, including disabled/excluded groups. Canonical output is a derived array of `{group, overrides}` dictionaries, not an Apple payload. Summaries show four groups/eight selected IDs each with escaped256-scalar previews. Library API: `effective_overrides::effective_groups_and_overrides`, `OverrideSettings`, `VariantGroupSettings`. This does not mutate settings, align native defaults, resolve content-override requests or apply selection.

`align-settings` uses the same original tool input as `effective-overrides`, with `gridGroupID` projecting the **effective** canvas mode (`storedCanvasMode ?? defaultCanvasMode`). It removes settings only when their canonical group IDs are absent from `groups`. Surviving enabled flags, original key spellings and all selection IDs remain unchanged, including stale IDs; discovered groups without settings do not gain defaults. A missing effective grid ID emits a directive to clear stored canvas mode. That directive may be a no-op when stored mode is already absent; it does not alter the default mode or choose another grid group.

Library `effective_overrides::align_settings` mutates the supplied OverrideSettings and returns Alignment (clear_stored_canvas_mode/removed_settings). It leaves mode values/persistence to the caller. The inspector reports the directive, removal count and resulting settings in deterministic NFD-key order; each selection uses the existing portable set order. These are derived tool outputs, not native serialization/order or persistence parity. Summaries show four settings/eight selection IDs each with escaped256-scalar previews. Full canonical output preserves complete surviving settings. No native alignment method is invoked.

`row-settings` reads the override UI row state for each input group. Existing settings win unchanged, even disabled/empty/stale selections. A missing setting reads as disabled with recursive configuration defaults, or an empty set without an override configuration. Reading does not install fallback settings. Library API: `OverrideSettings::row_settings(&group)` returns owned state.

The inspector shares the original groups/settings-array input format; optional gridGroupID is validated but does not filter row reads. Output is a complete derived array of groupID/isStored/isEnabled/selection dictionaries, not a native wire schema. Summaries show four rows/eight IDs each, escaped256-scalar previews. Recursive fallback inherits the documented deterministic portable default traversal and native sibling-representative difference. No private SwiftUI binding getter/setter, selection application or persistence is invoked.


`update-multi-selection` accepts an original inspector dictionary with required
`configuration` (override configuration wire value), strict Bool `isEnabled`,
String arrays `selection` (current state) and `requestedSelection`. It validates
all configuration children and every ID before calculation. Its derived output
contains `isEnabled`, `selectionChanged`, `selection`, and ordered
`childConfigurations`; this input/report is not an Apple wire schema.

The operation replaces child rows with configurations keyed by requested direct
variants, preserving variant order and duplicates. It unions their recursive
defaults with the requested set, preserves enablement and unknown IDs, and changes
stored selection only when canonical set membership differs. Equal membership
preserves existing ID spellings. The root's defaults are ignored. Child-added IDs
do not activate additional root rows. Repeated calls rebuild child rows even when
`selectionChanged` is false. The API returns the whole replacement row list; callers
own applying it, UI bindings, animation and persistence.

Summary output shows at most eight selected IDs and four child titles, each escaped
and capped at 256 scalars. Portable canonical ordering and recursive-default
representative policies remain scoped as documented above. The shipped private
SwiftUI setter has not been invoked; native UI animation and binding behavior
remain unverified.


`update-single-selection` shares the original update report and strict configuration,
`isEnabled` Bool and `selection` String-array input. It requires `requestedVariant`
String instead of `requestedSelection`. The chosen ID may be unknown or empty.
Starting with current selection, it removes every other direct root ID and the IDs
of that root's immediate child variants, even if that root was not selected. It
preserves unrelated IDs, grandchildren, orphan child values and existing values
under the chosen root. It inserts the chosen ID, rebuilds immediate child rows from
matching direct variants (including duplicates), and unions their recursive defaults.
Equal canonical membership preserves stored representatives; enablement is unchanged.
This is a calculation on owned state; native bindings/animation/persistence remain
unverified. Summaries retain the same bounded eight-ID/four-title policy.


`row-controls` accepts an original dictionary with required `group` (group wire
value), optional `settings` dictionary (required strict Bool `isEnabled` and String
array `selection`), and optional strict Bool `requestedEnabled`. Absent settings
use the disabled recursive-default row fallback. Reading leaves settings absent;
a delivered enablement write stores the complete row, even for an equal Bool,
preserving selection. This models a delivered setter call, not whether SwiftUI
suppresses, batches or coalesces a user event.

The derived output reports `isStored`, `isEnabled`, `selection`,
`enableWriteRequested` and `singleSelectionAvailable`. If available it also reports
`usesDefaults`, `candidates` and `portableValue`. Single-selection availability
requires a nonempty recursive default set, independently of enablement/style.
Stored IDs matching direct variants are eligible; absent matches use defaults,
which can include child or unknown IDs. Stored spellings survive canonical matches.
Native Set iteration picks one eligible ID; the inspector explicitly chooses the
first in deterministic decomposed-key order. With multiple candidates its value
may differ from Xcode. This is a per-call projection, not a retained SwiftUI binding
with a captured fallback or native-order parity. Summaries show at most eight stored
and eight candidate IDs with escaped256-scalar previews. No native binding or
persistence action occurs. The input and derived report are not Apple wire schemas.


`override-cache-keys` accepts an ordered array of existing content-override request
payload dictionaries (`contentCategory` String and required `requestedOverrides`
String array). It validates the whole batch before grouping requests by scoped
DestinationCapabilitiesCache.ContentOverrideKey identity. Category and each
positionwise override use qualified canonical Unicode equality. Array order,
duplicate count, empty arrays/IDs, case and compatibility distinctions matter.

`--canonical` emits the original derived report `representatives` (zero-based
first request index per equivalent key) and `uniqueKeys`; this is not native cache
serialization. Summary shows at most eight representative indices. The immutable
Rust key leaves wire spellings/order unchanged and supports Rust-local HashMap
memoization. Native hash bits, task coalescing, cache lifetime, error retention,
invalidation, fetch execution and transport behavior remain unimplemented. The
Unicode16 qualification and codec bounds/error-order limits remain inherited.


`task-cache` projects the recovered actor's serialized task-handle storage; it is
not an async executor or Apple wire format. Input is an original dictionary with
optional strict Bool `clearOnFailure` (default false) and required `operations`
array. An `acquire` operation requires `request` using the content-override payload
schema. It allocates a monotonically numbered synthetic handle only on a cache
miss and returns an acquisition ticket, indexed by acquisition order. A `failure`
operation requires a nonnegative `ticket` for one prior, unconsumed acquisition.
Only the creating ticket clears the key, and only with clearOnFailure enabled.
There is no task-identity guard: a late creator failure can remove a replacement.
A reused waiter failure leaves storage unchanged. Success needs no state change.

`invalidate` requires `request` and optional strict Bool `cancelingTask` (default
true). It records a cancellation request for a stored handle before removing it;
false removes without requesting cancellation. Cancellation is not completion,
waiter release or resource settlement. Removed handles remain valid for external
owners. All operations/requests/tickets validate before execution. Output reports
events, tasksStarted, retainedTasks and cancelRequests; summary shows eight events.

The generic TaskCache API takes host-owned cloneable handles/factory/cancellation
callbacks, and uses immutable content-override keys in the inspector. Hosts own
actual scheduling, task results, actor/executor synchronization, awaiting and
cancellation cooperation. Observe a failure only on the cache that produced its
ticket. The pure projection does not reproduce Swift actor reentrancy, priority,
executor hops or timing, and does not establish native/global resource parity.


`content_requests::content_override_task_cache` configures task storage with
clearOnFailure=true, matching the explicit DestinationCapabilitiesCache constructor
argument. The generic TaskCache default and task-cache trace default remain false.
Use host-owned task handles and provide the executor; neither factory spawns tasks.


### Grid request overrides

`inspect-content-result [--canonical] grid-request-overrides INPUT.bplist|-`
uses an original tool input: required `groups` (wire Group array), `settings`
(ordered `{groupID: String, isEnabled: Bool, selection: [String]}` entries), and
`gridGroup` (complete wire Group, projected from CanvasMode.grid's payload).
`gridGroupID` is unused for this command. All groups, settings and grid payload
validate before calculation, including disabled/excluded groups. Existing Unicode
16 canonical ID equality and codec limits apply.

Compute effective groups/overrides, excluding the grid ID. Exclude every remaining
group when its associated IDs contain the grid ID or the grid payload's associated
IDs contain that group's ID. Only direct links matter; no transitive closure or
lookup/replacement of the supplied grid payload. Flatten surviving override arrays
in source order, retaining duplicates and existing one-level child expansion.
Missing/disabled settings and missing override configurations keep their existing
skip behavior. State is read-only. Canonical output is the complete array of wire
Variant values. Text output shows counts and at most eight IDs, each bounded by the
existing 256-scalar escaped summary.

This is the grid branch's override calculation. It does not select a mode, apply
capability fallback, enumerate grid requests, construct PreviewRequest values,
launch previews or prove native lifecycle/rendering/resource parity. The original
public Swift Set/String composition qualifies the calculation; the shipped private
previewRequests method has not been invoked.


### Admitted request projections

`inspect-content-result [--canonical] request-projections INPUT.bplist|-` projects
ordered display modes, override arrays and optional grid variants after the native
method's earlier admission checks. Input is an original tool schema: `groups` and
`settings` as above, required `mode` dictionary and `capabilities` dictionary.
Mode discriminant is `live` (required `hostLocation`: `inCanvas` or `external`),
`grid` (required complete wire Group under `group`) or `static`. Capabilities
require strict Bool `supportsContinuousLivePreview` and `supportsStaticPreviews`.
The caller resolves stored/default mode and admission. `gridGroupID` is unused.
Inactive mode payloads are unused; all active payload/groups/settings validate
before calculation. These are projections, not native request/wire schemas.

Live always adds one interactive projection. Other modes add one when continuous
preview is supported. Its unnamed Bool payload is false for live external hosting,
true otherwise. Without static support, stop. With static support, append a
variant-less static projection for static mode or when no interactive projection
exists. Grid then appends a static projection per section variant, preserving order
and duplicates. Variant-less projections use all effective overrides (grid ID
excluded); grid-variant projections additionally exclude direct associations in
either direction. An empty/missing grid variants configuration adds no per-variant
projections. Continuous and static requests can coexist; this is not exclusive
fallback. Inputs are read-only; output values are owned.

Canonical output is an array of `{displayMode, overrides, variant?}`. Display mode
is original `{discriminant: "interactive", value: Bool}` or
`{discriminant: "static"}`; overrides/variant use existing wire Variant codecs.
Summary shows total count and at most eight display modes/override counts/variant
IDs, with existing escaped 256-scalar bounds. Preview instance, destination,
origin, control state, localization, request context/identity, earlier admission,
transport/execution and native lifecycle/rendering/resource behavior are omitted.
No complete PreviewRequest or native runtime parity claim.


### Settings-controlled request projections

`configured-request-projections` uses the request-projections input plus required
`defaultPreviewSettings` and optional `previewSettings`. Each is an original
`{isEnabled: Bool, boxedCanvasControlStates: [opaque plist values]}` dictionary.
The caller has already looked up the stored row using the actual structured
DiscoveredItem.ID.preview key; this command does not substitute a String key.
Both settings rows and all other active input validate before calculation, even
when disabled or a stored row makes defaults unused. Numeric Bools are rejected.
This tool validation policy is not a claim about native settings wire decoding.

A present stored row wins as a whole, even disabled or empty; otherwise defaults
win. Disabled yields no requests. Enabled uses admitted request projections and
copies the selected ordered control-state array into each request under original
report field `controlState`. No merge, deduplication or interpretation of elements.
Summary adds only per-request control-state counts, not their contents.

Core `PreviewSettings<T>::default()` matches the native constructor's disabled,
empty array. `configured_request_projections<T: Clone>` leaves boxed values/handle
cloning to the host. Original plist values demonstrate opaque array propagation;
native HashableBox/PlistValueBox codecs, equality/identity/lifetimes, full request
fields, persistence and resource settlement are not modeled or proven.


### Property-list value boxes

`plist-box` accepts a wire dictionary, retaining all fields and values without
requiring or typing `value`. Empty/unknown-only dictionaries are valid boxes.
`control-state-boxes` accepts an array of these dictionaries; order and duplicates
are retained, and every element validates before output. Canonical output preserves
the complete dictionaries. Summaries show counts/presence only, at most eight boxes.
These codecs do not unwrap boxes during wire decoding.

`unbox-string` requires `value` to be a String. `unbox-optional-string` returns
absence only when `value` is missing; present wrong types fail, while empty String
is present. Their canonical output is an original `{isPresent: Bool, value?: String}`
report. String summaries use the existing escaped 256-scalar limit. Unknown box
fields are ignored only by these typed getters and preserved by the box codec.

Core `PlistValueBox::required_with`/`optional_with` delegate present-value validation
to a caller codec, preserving its errors. `from_value` wraps one encoded value under
`value`; it does not reproduce the generic optional native constructor. The native
outer PropertyList is a String-keyed dictionary. As with existing dictionary codecs,
raw canonically equivalent outer key collisions are explicitly unsupported by this
portable adapter, although native bridging may collapse them. Nested opaque values
are retained. No native error-text, HashableBox equality/hash/identity/lifetime,
private method execution or complete control-state transport parity is claimed.


### Owned native box verification

`research/evidence/native-plist-box-2026-10-26/verify.py` rebuilds an owned ARM64
helper in a disposable directory, loads the pinned Xcode MessagingHost/FoundationHost
images, checks module offsets/runtime layouts and invokes actual box initialization,
encoding and required/optional String getters through an original C/assembly bridge.
Each native run has an eight-second deadline. It compares the full recorded native
results and counters, derives the conformance fixture, then checks Rust/WASI outputs.
Requires the pinned macOS ARM64/Xcode profile; portable Rust tests use saved fixtures.

The selected run covers eleven dictionaries and twenty-two typed outcomes. Explicit native
box/encoded-PropertyList destruction and error-release calls return. These are
scoped owned-value observations, not native UI/provider execution, HashableBox
identity/hash/equality or global resource settlement. The helper does not attach
to or modify Xcode/simulator processes. Source-only checks and actual invocation
results are recorded separately.


### Bounded native control-state equality keys

`control-state-keys` accepts an array of whole box dictionaries and returns original-tool
`representatives` (the first equal input index) and `uniqueKeys`. Summary output shows
at most eight representatives and no opaque state contents. All inputs validate before output.
`HashablePlistBox` retains the original `PlistValueBox` and separately caches its equality key.
Bool differs from numeric values; numeric equality follows the qualified projection below;
String/dictionary keys use qualified canonical Unicode equality; arrays retain order and
multiplicity; dictionary encounter order is irrelevant. Data and Date retain distinct types.
Rust-local hash values obey equality; native randomized hash bits are not reproduced.

The qualified Foundation-origin numeric profile supports full Int64/UInt64 and finite Real.
Native cached AnyHashable projections select Int64 for integral Real in [-2^63,2^63],
including saturation to Int64.max at real 2^63; larger integral reals below 2^64 select
UInt64. Remaining finite reals retain Double identity. This boundary preserves the observed
distinction between real 2^63 (projected Int64.max) and UInt64 2^63. Whole box roundtrips
retain the original real/integer type and value; only the cached equality key projects it.
The earlier conservative 2^53 restriction was superseded by actual cached-type observations
and expanded native comparisons. This is a qualified Foundation-origin profile, not a claim
about all possible Swift/object constructions of the generic native type.
The supported profile also excludes Null, nonfinite Real/Date values, canonical dictionary-key
collisions at any depth, and nesting beyond 64. These are portable domain restrictions,
not claims that the native initializer rejects those inputs. Generic Swift type identity,
unsupported Foundation objects, live state installation/transport and global resource
settlement remain outside this profile. Actual shipped HashableBox methods, 96 cached projections and 9,216 pair comparisons
are recorded in `research/evidence/native-hashable-number-2026-10-26`.


### Ordered Canvas control-state containers

`control-state-sequence-keys` accepts an array of state arrays. Each state array contains
whole box dictionaries. It returns original-tool `representatives` (first equal state index),
`uniqueKeys` and `states` (the complete original values after unboxing). Summary shows at most
eight state lengths/representatives with no opaque contents. The full input validates before output.

`CanvasControlState` owns an ordered sequence of qualified `HashablePlistBox` values and has an
empty default. Equality/hashing preserve order and duplicate multiplicity. Empty state differs
from a state containing an empty box. Numeric/Unicode equality uses the qualified box projection,
while value extraction preserves original wire values. Native Pipeline state construction/empty,
comparison/hash/destruction and copied-value reads are exercised in an owned helper after source
wrappers are destroyed. Native request Configuration.ID comparison delegates its control-state
part to the same ordered array comparison; complete request identity is not implemented here.
This original array adapter does not claim a native CanvasControlState wire schema, installation,
transport, provider execution or global resource settlement. Evidence:
`research/evidence/native-canvas-control-state-2026-10-26`.
