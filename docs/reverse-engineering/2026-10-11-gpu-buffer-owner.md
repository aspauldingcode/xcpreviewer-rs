# Isolating encoded Metal resource ownership from pool retention

The first owner-discrimination prediction failed: CPU-only, unencoded retained command, and unretained encoded command all left the weak buffer alive after setting the CPU variable to nil, just as the retained encoded command did. Draining the buffer construction/encoding pool before measuring weak liveness separates those cases. Only the retained encoded command then keeps the buffer alive while the command owner remains. This is a finite public-Metal ownership discriminator; it does not establish physical memory reclamation or Canvas policy.

## Retained contradiction and changed experiment

Baseline: macOS 26.5.1 (25F80), Xcode 26.6 (17F113), arm64, Apple M1 unified memory. Four modes each create a shared 16-KiB buffer initialized entirely to `0x5c`: CPU-only, retained-unencoded, retained-encoded, and unretained-encoded. Commands are never submitted. The encoded cases enqueue a fill operation but do not execute it. The unretained command is never committed with an expired buffer and expired weak objects are never dereferenced.

The initial same-pool control expected only retained-encoded to keep its buffer alive after the strong CPU variable dropped. Instead, all four weak buffer observations stayed alive until that pool drained, in both native runs. Six proposed negative outcomes therefore contradicted the prediction. Actual helpers exited zero: a zero exit alone does not make the failed prediction acceptable. The failed prediction, original source, actual waits, results and false acceptance assessment are sealed in `baseline/`, manifest `b1d713bfd982b3606f8cfb1c5e0d95615571f424c3e6bf207c0b0bc110ae7a0b`.

This does not falsify the previous reported liveness/weak-nil observations, which already excluded a sole-owner conclusion. It shows why same-pool liveness cannot by itself attribute retention to a command. Temporary/native autorelease-pool references are a confound; this experiment does not identify each internal holder.

The changed experiment creates the command/queue outside a nested construction pool. Buffer creation, initialization, encoding and temporary references occur inside that pool, which drains before weak buffer inspection. The command remains strongly owned. After the drain, CPU-only, retained-unencoded and unretained-encoded buffers are weak nil; retained-encoded remains alive at the original token and its full allocation is unchanged. Command status remains 0 for all command modes, with measured retained-reference policy true/true/false. After outer pool drain, both weak buffer and weak command are nil in every mode. Both repetitions agree.

Numeric tokens happened to repeat after prior weak nil and are only local tokens, never durable identity. No CPU data is read from a nil weak buffer; those `after` snapshots are null. All existing snapshots, including untouched padding/tail, are checked rather than comparing just the active fill region.

## Provenance and independent verification

Four native helpers run with unchanged 15-second subprocess/compile deadlines and a ten-second helper alarm under the exclusive controller lock. All actual waits are zero; there is no execution of a pending or expired-buffer GPU command. Initial contradictory controls and changed discriminator are retained together, not replaced with a success-only summary.

REA server `rea` / package `rea-agents` 6.2.0, started `2026-10-10T21:29:54.401Z`, separately binds both executed arm64 artifacts. Baseline SHA-256 `9a000b79609fcd161e496a8218f78115530b8eb84ab9a8d2f19a3e2aff29e7e5`, evidence `ev_3a6bd1e55401bf7494e759775cd4fddf1c62b739c75b6e7be44a78484d47a319`; isolated SHA-256 `cd326321d49e006410c4ea66e42e6fb2f8053db6875a469af8e31f3c1ca656f1`, evidence `ev_18d116a2aa74d3b13233717c2d7a79e8e9869aafb2c336d64eee815e847632b1`. Native utility provenance is retained and both target sessions are closed. Static identity and native helper observations remain distinct; registration alignment is not claimed.

The independent Python reader checks the inner baseline seal, failed assessment, actual waits and both ownership predicates. Twenty-six full allocations total 425,984 independently expected bytes (all `0x5c`), including row padding and tail. Six resealed wait, weak liveness, submitted-state, policy, expired-object snapshot and padding-byte-44 faults are rejected. The current helper source must match the frozen isolated source. Source/runtime control scope is finite and owned.

Evidence: `research/evidence/gpu-buffer-owner-2026-10-11`; manifest `7010b2175304947e02a515d44d895e02487dbc512da04a0ab7b6c3aad708db63`. Parent lifetime seal `9cb67c04646592908039c9a3f0f04e62fac07a56af58f8ab196f92d20affa4ea` was verified before selection. Publish only owned source, sanitized observations and metadata; executables remain local. Compile `tools/re/gpu_buffer_owner.m` with `xcrun clang -Wall -Wextra -fobjc-arc -framework Foundation -framework Metal` and execute with the same deadlines/lock to reproduce.

## Remaining acceptance

The isolated unsubmitted cases support a scoped causal ownership distinction between encoding and retained-reference policy. They do not authorize executing an unretained command after buffer destruction, prove timeout cancellation, measure IOSurface/Mach peer release or physical reclamation, or recover actual Canvas ownership. R1/R2 and both milestones remain open. The approved private bridge remains offline; no restart or Xcode workspace opened.

Next select a genuinely independent native failure/peer-release boundary or demanded product contract rather than repeating these owner/pool controls. Any future owner-lifetime measurement must isolate construction/observation pools; do not attribute liveness to a sole holder from a same-pool snapshot.
