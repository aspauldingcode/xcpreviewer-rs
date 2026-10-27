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
kill, purge, prepareToRelaunch, variants and contentOverride subsets. Other outer kinds fail explicitly. Default output is
human-readable `key=value` lines. String previews are debug-quoted, limited to
256 Unicode scalars and accompanied by UTF-8 byte count and truncation flag.
Absent strings print `absent`; an empty string prints `""`. Forwarding output
reports routing fields without dumping its arbitrary messagePayload. Content-override summaries show the total count and at most eight requested override strings. Canonical output retains the complete ordered array, including duplicates. Categories and override names are open strings; variants takes an optional single contentOverride while contentOverride requires requestedOverrides, even when empty. These are requests, not grouped variant replies or returned override results.

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

Modern shell requests use `messageType: update`; the inspector now decodes and canonicalizes them through `shell_service::ShellServiceEnvelope`. The optional identifier remains inside the shell payload. Summaries show only identifier and product/update counts. Nested multi-key incremental updates retain the explicit portable ambiguity rejection; nested nonfinite Real values use the qualified shell writer. This constructs/inspects request values and does not execute updates or establish daemon, Canvas or provider settlement. See `research/evidence/native-shell-service-2026-10-26` for actual native envelope and source dispatch evidence.

Use `inspect-service-message --prepare-update SHELL.bplist|-` to wrap a standalone qualified shell value as an `update` service request with a newly allocated process-local identifier. Output is canonical binary plist. Preparation invokes the reconstructed dispatch adapter with a value-only backend; it sends nothing and does not complete an update. New native/WASM CLI processes each start their own identifier sequence. Library callers can provide `ShellServiceTransport` to `dispatch_shell_update`; the backend owns its returned pending value, callbacks, scheduling and resources. Controlled native updater/reply evidence is in `research/evidence/modern-shell-dispatch-2026-10-27`.
