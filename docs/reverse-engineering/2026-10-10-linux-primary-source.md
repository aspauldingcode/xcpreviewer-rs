# Actual Linux execution of the primary-layer source subset

The 16 pinned source-derived standalone WASM modules and their native/model checkers execute on the existing Linux ARM64 Colima host with Wasmtime 49.0.0. All 64 fresh renderer allocations agree byte for byte with independent Fraction expectations and the macOS V8 captures: 1,048,576 bytes per comparison boundary. The 28 native-compatible frames additionally agree with the frozen native callback targets plus declared untouched tails: 458,752 full allocation bytes, including 20,160 measured native prefix bytes. These are reused native observations, not new native acquisitions.

The macOS source-to-C-to-saved-LLVM-IR compilation remains the pinned frontend. This work executes its exact output on Linux. It does not establish a Linux Swift compiler, arbitrary SwiftUI support, native getter/PNG equivalence, browser or Windows acceptance, independent non-Apple hardware, cheaper execution or Canvas wire semantics.

## Predeclared controls and results

- Two strides and two fresh instances per source module, including 1×1 and 64×64 geometries. Every 16,384-byte allocation includes active pixels, any declared row padding and the remaining untouched allocation. Full-capacity geometry has no tail; compact stride has no row padding.
- Four invalid renderer strides per module: zero, one below the active row, 257 and unsigned maximum. All 64 calls return zero and preserve the complete previous frame allocation, 1,048,576 bytes.
- Each source checker executes two strides and five modes, totaling 160 controls. The 32 baselines report zero; all 128 channel, alpha, row-boundary and final-allocation-byte faults report exactly one mismatch. Geometry determines whether those final offsets are padding, tail or active pixels. All 16 aggregates return eight only after checking every individual expected count.
- Four invalid checker index/mutation pairs per module: out-of-range stride index, out-of-range mutation and unsigned-maximum alternatives. All 64 calls return `0xffffffff` and preserve the entire 131,072-byte linear memory. The 8,388,608 compared bytes include constants and scratch space as well as pixels. These comparisons use each checker's observed post-valid-call baseline, not an independently predicted full compiler memory layout.
- Host verification checks source text against its declared configuration, saved IR/module hashes, exact record order/count/type, V8 checker counts, native/model frames and invalid-call bytes. Rehashing corrupted pixel, alpha, padding or tail files cannot make a comparison pass. Missing/truncated inventories, boolean integer metadata and checker count changes fail verification.

## Retained failure and correction

The first execution established the original positive/frame/renderer-invalid/fault boundary. An expanded control incorrectly assumed the checker exported `pixels` and `capacity`; it failed with `KeyError: 'pixels'`. The sealed failure is retained. The checker only exports `verify`, `verify_all` and memory. The corrected probe uses its actual exported memory and verifies all 128KiB against a captured valid-call baseline, without changing or relinking the pinned modules. The complete corrected run supports the expanded contract. The failure is excluded from graph completion and is not an integrity quarantine.

## Identities, isolation and evidence

Host identity: Linux `6.8.0-100-generic`, aarch64, Wasmtime 49.0.0, existing Colima VM on Apple hardware. Pinned runtime wheel SHA-256 `263b924576d9519c43d5a1acff50a03ab03209d16d26c53543c9ab9a409fb93f`; every extracted runtime file is checked against the wheel. Existing image SHA-256 `4d93e034ce6cd5ed51447f399bc76b0d9b45fcb47dd0175ee928a3848ab35109`. No image pull, network, VM lifecycle change or package install. Owned read-only containers have no capabilities, bounded CPU/memory/PIDs and a 45-second subprocess deadline; each WASM call has 10 million fuel and 128KiB memory limits. Ownership labels authorize cleanup only for the generated container. Cleanup succeeds even for the retained failed run. Both existing containers remain running. No Xcode window opens.

Source anchor: `20261010T191804Z-portable-primary-source-subset-811cf568`, manifest SHA-256 `45f7ac0b391eb74b2580209a237e231ee77d55be31c2857129c14137d69b3f88`.

The three current manifests and sanitized observations are in [Linux primary-source evidence](../../research/evidence/linux-primary-source-2026-10-10.json). The corrected complete run is `20261010T192727Z-linux-primary-source-subset-b075e295`, manifest SHA-256 `10215ed49eee6c5d19bc7be1432c9b7d9d175598b623e41227d693cad50d4182`. All seals verify against their separately recorded hashes. Both milestones and F1 remain open. Next: actual browser execution and its explicit premultiplied-to-Canvas2D boundary, preserving native getter/PNG differences.
