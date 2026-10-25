# Inspect reconstructed service-message values

Run the standalone inspector from the repository:

```sh
cargo run --offline --manifest-path tools/re/rust/canvas-core/Cargo.toml \
  --bin inspect-service-message -- INPUT.bplist
cat INPUT.bplist | cargo run --offline \
  --manifest-path tools/re/rust/canvas-core/Cargo.toml \
  --bin inspect-service-message -- --canonical - > normalized.bplist
```

Input is `bplist00`, from one named file or standard input (`-`). The inspector
supports the recovered ping, capabilities, connect, forward, cancelUpdate, stop,
kill, purge and prepareToRelaunch subsets. Other outer kinds fail explicitly. Default output is
human-readable `key=value` lines. String previews are debug-quoted, limited to
256 Unicode scalars and accompanied by UTF-8 byte count and truncation flag.
Absent strings print `absent`; an empty string prints `""`. Forwarding output
reports routing fields without dumping its arbitrary messagePayload.

`--canonical` emits only a normalized binary property list on standard output;
errors go to standard error with a nonzero exit status. Normalization follows
`ServiceEnvelope`: unknown fields are omitted, missing purge killAgents becomes
false, missing forward orientation becomes portrait, and failed capability
content decoding becomes absent capabilities. Identifier errors still reject.
Prepare-to-relaunch retries legacy agentIdentifier after any agentDescriptor error; descriptor decoding also retries a flat bundle with an empty relaunch ID. Canonical prepare output includes a modern descriptor and legacy bundle. Bundle discriminants are ignored during decoding and recomputed from optional path presence. Paths and bundle IDs are opaque strings; no files or agents are resolved. Full UInt64 update seeds are retained. This is semantic normalization, not a
lossless archive editor or a byte-identical Foundation serializer. A failed
output write may leave partial stdout, so check the exit status before using it.
Input is limited to 64 MiB; existing codecs also enforce object/depth/output
budgets. No identifiers are allocated by inspection.

The same executable builds for `wasm32-wasip1`. Standard-input operation needs no
filesystem preopens; file input requires the WASI host to grant that directory.
Actual WASI verification uses no preopens and no inherited environment. Browser
WASM execution is not established by this check.

These commands inspect and encode values only. They do not contact Xcode, send
requests, verify peer liveness, cancel updates, purge agents, control processes
or prove provider/resource settlement. Native schema evidence remains scoped to
the linked service-envelope evidence chain; the CLI itself is original tooling.
