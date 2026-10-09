# Verifiable output and exact compatibility

The acceptance target is a replayable, independently checked compatibility report for a declared set of inputs. A program comparing its own output with itself establishes repeatability, not correctness. A hash establishes identity, not semantic correctness. Finite experiments do not prove all possible behavior.

## What is compared

| Boundary | Reference and candidate | Acceptance rule |
| --- | --- | --- |
| Captured artifacts | Original file versus replayed file | Every byte equal, including length. Report SHA-256, differing byte/bit counts and first mismatch offsets. No normalization. |
| Serialization | Apple UVPropertyList versus repeated call, fresh object, Foundation, and Python encoder | Record each byte comparison separately. A semantic round trip cannot satisfy byte compatibility. Foundation and UV may share implementation; they are not assumed independent. |
| Decoded values | Original typed fixture versus independent Python decoding of Apple output | Types, float64 bits (including signed zero), bytes, dates, arrays and dictionary contents agree. Dictionary order is a semantic distinction only when the contract requires it. |
| Rendered files | Apple PNG versus another capture or candidate PNG | Exact file comparison is distinct from decoded pixel comparison; PNG compression and metadata can differ. |
| Rendered pixels | Same geometry and ICC profile, RGBA conversion only | Every channel agrees at threshold zero; incomparable geometry/profile cannot satisfy an A/A control. A tolerance is a separately named acceptance tier and never reported as bit exact. |
| State and IPC | Original native session versus implementation replay | Preserve raw envelopes, attachments and lifecycle. Compare decoded fields and causal ordering using an explicitly specified model. No complete implementation or captured IPC oracle exists yet. |
| Tool output | Frida events versus Ghidra image/function | Binary hash, Mach-O UUID and unslid function offset agree. This validates linkage; decompiler output is not a behavioral oracle. |

The initial 24-case serialization audit preserved all typed values. All 24 repeated/fresh UV serializations matched Foundation bytes; all 24 also matched a second helper process. Python's encoder matched Apple bytes in only six cases. The other 18 are real encoding differences, not failures of decoding. Python encoding must therefore not be substituted for an exact Apple encoder without further work. These counts describe this corpus and environment only.

Three small synthetic goldens are committed under `tools/re/fixtures/PlistOracle`: Unicode/NUL, integer boundaries, and booleans/float64 signed zero. Each has original Python-encoded input, Apple-encoded reference, lengths, hashes, probe provenance, environment and sealed-run manifest anchor. They contain no captured private preview traffic. After a new corpus run, an independent system comparator can check a regenerated Apple output:

```sh
cmp tools/re/fixtures/PlistOracle/boundary-04.reference.plist research/runs/RUN_ID/output/boundary-04/base64.plist
```

Exit zero means every byte matches. Keep the original golden when a new target differs; record a new version and explain the change.

## Oracle before implementation

1. Pin original binary/UUID, OS, Xcode/compiler, architecture, source, locale, display scale, fonts, appearance and rendering settings. Preserve actual settings and hashes, rather than a model's recollection.
2. Create owned minimal fixtures. Vary one factor at a time. Include empty values, integer boundaries, signed zero, Unicode, nested containers, large data, invalid messages, cancellation, restart and resource release. Malformed IPC and attachment cases require a recovered transport first.
3. Capture Apple reference A twice without changes, including separate process and cold/warm cache runs. If A/A differs, report nondeterminism and identify its source. Never manufacture a golden by averaging or silently masking differences.
4. Capture controlled variant B. Confirm expected change and unchanged invariants. This positive control detects a capture accidentally reusing a cached image.
5. Freeze reviewed golden inputs and reference outputs before changing the candidate. An agent must not update goldens merely to make its implementation pass. Keep holdout fixtures separate from implementation feedback.
6. Replay identical inputs through the candidate. Run byte, typed value, pixel and lifecycle checks separately. The report includes failed and inconclusive checks, unsupported features, and coverage denominator.
7. Inject known faults: flip a bit, truncate an envelope, change a discriminant, drop/reorder a required event, leak an attachment. A checker that cannot reject the injected fault is insufficient for that boundary.
8. Shrink failures while preserving the exact failure predicate. Save original and minimal fixtures. A tool crash is not a semantic mismatch, and a failed capture is not a candidate failure.

Addresses, PIDs, timestamps, concurrent scheduling and linker UUIDs can vary legitimately. Keep their original bytes. A separate semantic view may map addresses to image UUID + offset or compare causal order, with every transformation declared. Such a view must never be called byte exact. Different target architectures are not expected to produce identical executable bytes.

## Evidence and trust

Each controller run freezes worker sources, experiment, inputs, environment, journal, outputs and artifact hashes. `re_verify` checks consistency against its manifest. `re_compare` compares two sealed artifact references, streaming every byte. `re_verify_anchor` also checks a manifest SHA-256 supplied from a separately trusted location.

CLI examples (replace IDs, paths and digest with reviewed evidence):

```sh
research/venv/bin/python tools/re/agent.py verify RUN_ID --manifest-sha256 TRUSTED_DIGEST
research/venv/bin/python tools/re/agent.py compare REFERENCE_RUN output/reference.plist CANDIDATE_RUN output/candidate.plist
```

Both commands return nonzero on mismatch. A successful comparison against the same artifact is only a comparator sanity check, not an independent compatibility test.

An editable local manifest cannot authenticate itself. Rewriting both an artifact and its recorded hash can produce a self-consistent forgery. Publish reviewed manifest digests in the small Git evidence index; use a trusted commit/reviewer copy as the external anchor. A plain remote Git branch is not an immutable trust root. Sign releases or retain an independently trusted commit/hash when stronger authenticity is required. Hashes do not certify that instrumentation captured every event.

Large raw evidence stays local. SQLite search returns snippets and artifact references; exact pages remain retrievable with hashes. MCP previews are bounded to approximately 6,000 characters, not a promised token count. Even compactable responses retain a content-addressed full original. Claims reference sealed observations and explicit scope; failed tools remain inconclusive. No model-generated confidence score substitutes for a reference check.

## AI automation at the difficult boundaries

| Edge case | Automated response | Human or native oracle needed |
| --- | --- | --- |
| Xcode/OS/ABI drift | Fingerprint changes invalidate previous completion; re-resolve symbols and run narrow probes | Confirm newly recovered signatures; never guess Swift ABI |
| ASLR, pointer authentication, PID reuse | Join UUID/hash/offset; verify process start identity and owned mapped image | Protected processes remain outside tracing scope |
| Late hooks, dropped messages | Record capture coverage and gaps; retry pending mappings; retain errors | Establish complete request/reply correlation before protocol claims |
| XPC/IOSurface handles | Future replay must retain descriptors, ownership and release order | Bytes alone cannot replay kernel resource capabilities |
| Stale preview/cache or wrong scheme | Exact owned project tab, build settings, A/A and A/B controls | Native build/render diagnostics distinguish harness failure |
| Float/date/Unicode type changes | Seeded typed corpus, boundary cases and deterministic shrinking | Expand corpus from real observed failures |
| Fonts, DPI, ICC, animations, GPU variance | Zero-threshold image comparison with explicit geometry/profile rejection | Classify rendering nondeterminism before setting tolerances |
| Hallucinated protocol behavior | Evidence-linked scoped claims and counterexperiments; quarantine tampered runs | Review recovered semantics against native behavior |
| Infinite failed retries / context growth | Error fingerprints, bounded templates, session watchdog, local search/paging | Choose a changed hypothesis; no automatic budget renewal |

Current automated tests deliberately exercise bit flips, truncation, streaming boundaries, signed zero, changed evidence, rewritten manifests and graph provenance. Native fixtures separately test the actual Apple serialization and Frida/Ghidra paths. Complete wire replay, attachment validation and portable renderer conformance remain future milestones; they cannot yet be certified bit for bit.

## Fast ports and efficient investigation

Recent projects illustrate different starting points. [Generals](https://github.com/ammaarreshi/Generals-Mac-iOS-iPad) builds on released source and existing porting work, with DirectX translation through DXVK/MoltenVK; it is not reconstruction of an entire game from machine code. Its [porting playbook](https://github.com/ammaarreshi/Generals-Mac-iOS-iPad/blob/main/docs/port/PORTING_PLAYBOOK.md) stresses finding the strongest existing base and validating platform behavior. [Bumpy](https://github.com/GeReV/bumpy-reverse) describes AI-assisted instrumentation, emulation and differential validation alongside human correction and visual testing. [Masquerade](https://github.com/zpqrtbnk/masquerade) reports that early translation filled unknowns with guesses; building a knowledge base and emulator tooling first improved the second attempt. These are authors' reports, not independent benchmarks or universal porting-time guarantees.

Apply that pattern here: choose one narrow native preview, obtain a reliable oracle, recover the smallest supported boundary, then implement and replay it. Keep existing compiler, image and analysis tools. Avoid a full SwiftUI/WASM rewrite before knowing the required semantics. A working vertical slice with rejected unsupported features is a better next milestone than a broad unverified implementation.

For token efficiency, the controller computes hashes, diffs, validation and shrinking locally. The agent reads a compact checkpoint, searches symbols/evidence, retrieves only the relevant function or mismatch, proposes one discriminating experiment and records a small scoped claim. Cache by binary/source/environment identity; reuse valid completed runs. Batch independent reads, avoid whole-binary dumps, and escalate model effort only for unresolved hypotheses. Measure tool-result characters and actual model token usage separately; fewer tool-output characters do not establish a fixed percentage saving. Local tools are free; model inference is not guaranteed free.
