# Primary-layer source CLI and transactional build cache

`tools/re/source_cli.py` builds the declared ASCII primary-layer `ZStack.frame` expression subset into standalone WASM. Unsupported source fails with a structured error; no Apple framework execution fallback exists. Compiler and named WebAssembly linker paths are explicit arguments. This build adapter is currently verified on macOS with repository Python dependencies and POSIX file locks; no Windows or Linux frontend execution acceptance is claimed.

Example from the repository root:

```sh
research/venv/bin/python tools/re/source_cli.py owned.swift \
  --cache /tmp/owned-primary-cache --output /tmp/owned-primary-output \
  --clang /path/to/clang --wasm-ld /path/to/wasm-ld
```

The input must fit4096 bytes and satisfy the existing strict parser. Compiler stages each have a30-second deadline. Compile invocations use argument arrays, not shell interpolation. Output is an immutable-by-contract version bundle containing lowered C, normalized saved LLVM IR, WASM and their manifest. A single atomic `current.json` pointer selects the published bundle only after compilation, cache integrity checks and copying succeed. Consumers must resolve that pointer and verify the named bundle before use. No running consumer or runtime instance swap is implemented here.

## Cache and source identity

A canonical key binds parsed source semantics, target, every compile/link option, producer/normalizer/lowerer code hashes, lowered kernel bytes, actual compiler/linker bytes and their invocation paths. Whitespace-only changes to the accepted grammar share the semantic cache entry, while the exact input source hash changes in the published receipt. A layer-order change creates a new key and module. This policy is safe only for the declared literal grammar; it is not arbitrary Swift semantic equivalence.

An index separately pins the content-addressed entry manifest. Exact inventories, manifest/payload hashes and sizes, typed schema, regenerated lowered C and WASM header are checked before reuse. Entry/index/publish symlinks are rejected. Nonblocking owned cache/publish locks prevent concurrent writers. Staging directories are removed on errors. Local consistency is not cryptographic authenticity: an actor replacing the entire cache and index is outside this claim. Runtime/native conformance comes from independent sealed observations.

## Discriminating experiments

Four CLI calls cover a cold build, exact cache hit, whitespace cache hit with distinct source provenance and a changed layer-order cold build. Every saved IR and module byte must equal its independently pinned primary-source output. The four published modules then run in16 fresh V8 instances across two strides/two repeats. All262,144 allocation bytes match independently recomputed Fraction expectations;8 native-compatible frames additionally match5760 reused native callback-prefix bytes and their complete declared tails.16 invalid renderer requests preserve all262,144 allocation bytes.

Seven failures must leave the previous published pointer and module bytes unchanged: unsupported source, corrupted cached module, corrupted manifest, invalid cache-index path, failing compiler, generic linker invocation and a deliberate pre-publication fault. This is a bounded build/publication transaction control. It does not establish a hot-reload watcher, debounce, running-instance replacement, state migration or stale-generation handling.

The first sealed run failed before the first publication. Diagnosis found that resolving `wasm-ld` to its symlink target changes the driver invocation to generic `lld`, which rejects the link. The corrected adapter preserves the named launcher and binds its invocation to the cache key. A subsequent deliberate generic-driver control retains the exact error and confirms last-valid publication preservation. Compiler-call stdout/stderr and exit outcomes are now retained for positive and negative controls. Failures are retained and excluded from completion; seals remain valid.

The complete final run also binds builder/IR-normalizer identities and every linker option. Earlier supporting runs are narrower checkpoints. See [sanitized evidence](../../research/evidence/primary-source-cli-2026-10-10.json) for manifest hashes and observations. Native getter/PNG differences remain unresolved and separate from this explicit premultiplied callback-target contract. Both milestones and the build-adapter issue remain open. Next independent slice: declared source-to-frame/image CLI with bounded runtime and failure controls, without attempting the blocked browser.
