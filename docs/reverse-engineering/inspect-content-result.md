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
Browser execution, private decoder/runtime parity, whole grouped replies and full override-selection configurations, and
actual rendering/lifecycle/resource settlement remain outside this result.

## Single-select configuration

Use `inspect-content-result single-selection INPUT.bplist` (or `-` for stdin) to inspect an individual SingleSelectConfiguration. Add `--canonical` before the kind to emit normalized binary plist stdout. Both `style` and `defaultVariant` are required strings. Style must be `list` or `range`; defaultVariant is an opaque ID, including empty or unknown strings. Style errors precede default-ID errors. Unknown dictionary fields are omitted from canonical output. Summaries escape IDs, cap them at 256 Unicode scalars and report original byte length/truncation; canonical output preserves the complete ID.

This mode does not choose or apply a variant, check membership in another configuration, decode full override configurations or decode grouped replies. Multi-select default IDs use a native Set; equality, representative retention and serialization ordering remain to be qualified before implementing that branch.
