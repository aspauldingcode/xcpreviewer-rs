# Local XPC coding boundary — 2026-10-08

Four sealed follow-up experiments support a narrow, reproducible model of `UVPropertyList` coding. The owned helpers construct local XPC dictionaries; they never connect to a service or transfer a resource. See the [machine-readable results and external manifest anchors](../../research/evidence/xpc-boundary-2026-10-08.json).

For all 32 fixed/seeded dictionary cases, `encodeToXpcDictionary:` inserts exactly one field, `data`, of XPC data type. Its bytes equal the object's `data` property. Native decoding and independent Python decoding preserve typed values; a second helper process produces identical bytes for all 32 cases. The Unicode case also matches the earlier independently collected plist oracle: 104 bytes, zero differing bits, SHA-256 `44466988eec03bccdf8abcb807ff11336cf558d1f0974c1bef47f40f09555350`. System `cmp` independently confirmed equality with the published plist golden.

## Malformed inputs

| Owned input | Observed result |
| --- | --- |
| Missing XPC `data` | nil |
| Wrong XPC field type | nil |
| Empty XPC data | nil |
| Nonempty prefixes 1–103 of the 104-byte Unicode plist | decoded empty dictionary |
| Full 104-byte plist | original typed values |
| Full plist plus an extra XPC key | original typed values |
| Direct `initWithData:` with empty data | decoded empty dictionary |
| Direct `initWithData:` with eight-byte `bplist00` | decoded empty dictionary |
| Direct `initWithData:` with full 104 bytes | original typed values |

The prefix sweep executes all 105 lengths, with zero helper failures. Shrinking preserves the unexpected empty-dictionary fallback with one input key. The [small synthetic golden](../../tools/re/fixtures/XPCOracle/manifest.json) records that reproducer and both native control anchors. Python `plistlib` rejects its eight malformed bytes with `InvalidFileException`; strict parser behavior therefore differs from this native decoder. A compatibility implementation must explicitly model the chosen malformed-input behavior and test it against the oracle. Do not update goldens to hide a difference.

This measures one installed OS PreviewsServices image, UUID `FFFB683F-5943-3C25-91B2-72D6E5174FA3`. The malformed-input sweep covers one plist, not every corruption or every possible dictionary type. A one-field local coding result does not establish the complete service envelope, dispatch behavior, attachments or resource lifetime.

## Static message strings

A bounded ARM64 interpreter follows the selected `AgentMessageType.rawValue` getter and corroborates returned strings against independently parsed Swift field descriptors. It rejects calls, unknown instructions, unmapped reads and execution beyond its budget. It recognizes only the observed immortal ASCII small-string and large-literal forms, using the public [Swift StringObject representation](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/StringObject.swift) to interpret those forms.

Ten unique returns match the ten case names:

- `previewInstances`, `incrementalPreviewInstances`
- `render`, `incrementalRender`
- `display`, `incrementalDisplay`
- `layerHost`, `incrementalLayerHost`
- `captureIOSurface`, `incrementalCaptureIOSurface`

Pinned host image SHA-256: `0413e01c6a94d3733b3778ce212fafb24fd62c67b071486604422cfd472df88c`; Mach-O UUID: `ce1040273729381b8f0cc774e404c0ce`. Internal enum selectors are not numeric wire IDs. These static strings still require validation in an actual captured envelope.

## Loop and verification

Four new reviewed adapters connect these experiments to the serial controller, frozen-source worker, strict checks, evidence index, scoped claims and next-experiment planner. The planner recognizes malformed-input fallback and proposes a prefix counterexperiment; already queued experiments resolve to reviewed work instead of duplicate proposals. There are 16 adapters and 19 MCP tools. The expanded offline suite passes 52 tests, including strict bool/int distinction, capture truncation, exact payload comparison, bounded static interpretation and published golden hashes.

Initial attempts remain sealed: one static result supported its assertion and three native results were inconclusive because the harness capture limit excluded 64 KiB payload overhead and a boolean was boxed as an integer. Both harness errors were corrected, with explicit regression tests, before the four final experiments. All final artifacts and frozen sources verify. Published manifest hashes anchor the local evidence; authentication still requires a separately trusted commit or reviewer copy. Raw binaries, full disassembly and byte dumps remain local.

Three bounded Xcode bridge diagnostics distinguish successful initialization from a stalled `tools/list`: no workspace, an owned project open, and a fresh documented session ID pinned to the running Xcode process. All time out at schema discovery. No settings were changed. Stop unchanged retries; next canvas work needs a responsive bridge or an independently verified capture path. Full request/reply correlation, attachments, A/A canvas stability and controlled A/B rendering remain open.
