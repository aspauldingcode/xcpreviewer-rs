# Binary preview payload reconstruction

The original portable Rust core now accepts binary `bplist00` bytes and decodes them into the recovered RenderPayload, BitmapDescription, SelectableRegion and flat CGRect models. A `decode-preview-payload` CLI prints metadata and optionally writes the exact bitmap data, retaining row padding.

This extends the current shipped-code recovery in `research/evidence/direct-bitmap-region-2026-10-19` (seal `7c81f632fabe960208d750d99f0255a50a25c7199fb81b89428582a4bb0de789`). That evidence was reverified before sealing this result. No new private runtime, injection, UI or Xcode MCP operation was attempted. No unchanged Frida attachment failure was repeated.

## Independent checks

`generate_fixtures.py` uses Python's standard-library plistlib serializer, without importing the Rust parser. Four original fixtures include nested preview dictionaries, Unicode and a surrogate pair, long data/string lengths, integer/real/null/bool scalars, and 300 distinct objects forcing two-byte references. The first three fixture hashes reproduce the preimplementation fixtures exactly. Handwritten binary cases exercise float32, malformed references/text/keys, duplicate dictionary keys, cycles, unsupported types, recursion and DAG expansion limits. All 415 strict prefixes of the default fixture and all 256 marker values are exercised without panics.

All 23 Rust tests pass (16 existing plus 7 binary-input integration tests). The CLI independently exports each preview fixture's complete 80-byte bitmap and compares every byte with Python's expected bytes: two rows, each 12 active bytes and 28 synthetic padding bytes. This is synthetic padding preservation, not a native allocation or captured Canvas frame claim. CLI metadata checks confirm the recovered default corner 0 / scale 3 and explicit corner 6.5 / scale 2. Malformed input exits 1 before replacing an existing output.

## Usage

From the repository, with an installed Rust toolchain:

```sh
cargo run --offline -p canvas-core --bin decode-preview-payload -- tools/re/rust/canvas-core/tests/fixtures/payload-defaults.bplist /tmp/preview.bitmap
```

The command does not interpret pixel channels, render a view, or assert the input is a captured native message. It exposes the recovered payload data for subsequent renderer and transport integration.

## Format and limits

The binary container format reference is [Apple CF's public marker/trailer declarations](https://github.com/apple-oss-distributions/CF/blob/main/ForFoundationOnly.h); [Apple's binary parsing example](https://github.com/apple/swift-binary-parsing/blob/main/Examples/BPListParser/BinaryPList.swift) is a separate reference. The implementation is original Rust with no added dependencies and forbids unsafe code.

Supported values: null/bool, 1/2/4/8-byte integers, float32/64, data, ASCII/UTF-16 strings, arrays and string-keyed dictionaries. Date, UID, set and 16-byte integer forms return explicit unsupported errors. XML plist input is not implemented. The parser caps object count/expanded visits at 100,000, depth at 64 and copied data/text budget at 64 MiB. The CLI separately bounds input reading to 64 MiB. Duplicate keys are rejected; offset tables must end at the trailer. These are reconstruction policies, not recovered Foundation malformed-input/coercion behavior. Explicit real values remain required for CGRect and optional scale/corner fields by the typed adapter.

## Remaining work

Connect validated bitmap metadata/data to rendering and selectable-region input; independently test interpretation of flags, row stride and color space. Recover and correlate actual lifecycle/transport packets using a changed permitted observation route. XML and additional plist types should be added only when their input requirement is established. Both milestones and native R1/R2 acceptance remain open; successful parsing/building is not behavioral parity.
