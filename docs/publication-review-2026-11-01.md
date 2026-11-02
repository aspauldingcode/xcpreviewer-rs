# Public source synchronization review

User explicitly authorized making aspauldingcode/xcpreviewer-rs public and synchronizing local source on 2026-11-01 (America/Los_Angeles). Pages must use this original repository.

The fetched Git history scan covered 16,832 reachable objects, including 10,515 blobs / 143,407,912 uncompressed blob bytes. No tested credential signatures, large raw disassembly blocks or common decompiler dumps were detected. This is heuristic triage with provenance review, not a claim of exhaustive security proof. Four historical native binaries match owned observer/Rust test-tool build manifests and SHA-256 receipts; none is a shipped Apple binary. The observer provenance points to owned OwnedProcessSnapshot.c; the three Rust artifacts match frozen original Rust source/manifest records.

The local synchronization snapshot contains 2,305 files / 24,033,096 bytes before publication bookkeeping updates. It includes original reconstruction sources and owned/sanitized evidence. Native DerivedData/compiler caches (about 53 GB logical size) and the identified complete-row-getter.s raw Apple disassembly remain ignored/local. Existing raw/runtime/build/ghidra directories remain ignored. No secret values were emitted in audit reports.

Validation from the isolated source snapshot: full offline Rust cargo test suite passes, 21 focused Python tests pass (watcher, process observer and source-frame adapter), and six browser-follow controls pass. First cargo invocation failed because cargo was absent from PATH; rerun with the installed toolchain's absolute paths passed. Existing unused-field/import warnings remain. Native experiment receipts are retained at their original declared scopes; these tests do not re-run every historical native capture or close Canvas parity.

The user's original staged index is preserved. Publication is performed from an isolated checkout, with fast-forward development/master pushes and no force push or history rewrite. Historical pending-publication records remain historical; this explicit authorization and synchronization ledger supersede their pending authorization status for the reviewed source snapshot. Native Canvas recovery remains 0/9 fully accepted areas; delivery tracker remains 1/26 tasks closed.

Pages uploads only index.html, style.css, app.js and refreshed status.json. No binaries, raw disassembly, compiler caches or private captures enter its public artifact. The full source repository is public by explicit user choice.
