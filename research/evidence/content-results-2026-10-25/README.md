# Individual preview variants and selected-override results

Recovered and implemented complete scoped value codecs for RenderEffect,
PreviewVariant and ContentOverridePayload, with an original bounded
inspect-content-result CLI. Select variant or override explicitly. No request
correlation, grouped reply acceptance or application of effects is implied.

PreviewVariant first reads optional renderEffects. If absent, it requires
legacy renderEffect and wraps it into a singleton array. A present malformed
array rejects without legacy retry; a present empty array stays empty and wins
over any malformed legacy value. Each effect dictionary requires a String id.
Only after effects does the decoder require variant id and displayName strings,
then optionally decode interfaceOrientationOverride. Orientation has four exact
raw values: portrait, portraitUpsideDown, landscapeLeft, landscapeRight. No
orientation value is synthesized for absence. IDs are opaque open String
wrappers; resolving an effect or rendering it remains unimplemented.

The encoder writes both modern effects and a legacy single effect. That legacy
value is the first array member; for an empty array it uses the exact literal
id="Missing". This is compatibility data, not a successfully applied effect.
Canonical output preserves order, duplicates, empty IDs and optional orientation
presence. ContentOverridePayload reads optional contentOverride: absence is a
valid result and explicit empty string remains present. Present non-string
values reject. Unknown fields are omitted, so a caller-selected unrelated
dictionary can decode as absent override; this does not establish reply identity
or successful override application.

Source evidence: current MessagingHost SHA/UUID and FoundationHost SHA verified.
All 2,208 selected bytes independently matched LLVM: field descriptors/raw key
getters, optional modern array and legacy-required branch, required ID/name,
optional orientation, first/empty-array legacy encoder, required RenderEffect
ID, open String-copy initializers, strict orientation raw range and optional
selected-override decoder/encoder. Exact nlist definitions resolve folded alias
labels. Raw Apple disassembly and symbols remain local ignored files only.

Runtime evidence is 29 original public Foundation cast/serialization controls
plus original source-guided composition, not private decoder execution. Sixteen
accept and thirteen reject. Controls cover missing/empty/ordered/duplicate
modern effects, malformed modern array and elements, valid/invalid legacy
values, modern precedence, empty IDs/names, Unicode/control text, required
fields, all four orientations plus unknown/wrong-type orientations, long effect
arrays and absent/empty/unknown/malformed selected override. All 281 Rust tests
pass; four new tests cover complete expected values/round trips, error order,
compatibility placeholder, actual CLI output, argument handling, file/stdin
agreement, escaped/bounded summaries and 64 MiB+1 rejection.

Actual Node WASI runs all 29 canonical cases and sixteen accepted summaries
(45 invocations), with explicit stdin/stdout handles, no filesystem preopens and
no inherited environment. Accepted canonical values match complete type-sensitive
expected results and pass sixteen public Foundation reparses; rejected cases
emit no binary stdout. Accepted summaries match native bytes. Disposable replay
repeats source checks, the four new tests, Foundation controls and actual WASI;
full 281-test output is retained separately. No new verification failures in
this unit. Direct private Swift import remains unavailable under the previously
recorded shipped framework search path; no repeated import or guessed ABI call.
REA package/path/catalog identity checked against the retained expected tuple;
provider readiness remains a separate question, with no repeated inventory loop.

Group recovery started but is explicitly not a codec here. Metadata identifies
PreviewVariantGroup fields id, associatedGroupIDs, overridesConfiguration and
variantsConfiguration. Its wire key is associatedGroupIDsArray. Group decoder
uses optional configuration decoders and Set construction for associated IDs;
those details need separate complete qualification. PreviewVariantsPayload
requires a group array, and depends on PreviewOverridesConfiguration,
PreviewVariantsConfiguration and their selection/section types. Their pending
status is retained in dependency-graph.json. No partially typed group is
silently accepted by the new inspector, which requires one individual entry.

Private decoder parity, complete grouped variants/configuration/reply behavior,
request matching, actual rendering/refresh/lifecycle/provider cleanup, global
resource settlement and both milestone contracts remain open. CLI usage is in
`docs/reverse-engineering/inspect-content-result.md`.
