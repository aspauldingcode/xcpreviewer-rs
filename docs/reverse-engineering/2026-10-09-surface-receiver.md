# Receiver-first surface exit and retained-port access

A sealed owned Mach handoff campaign passes eight receiver-first cases: four CPU BGRA shapes under clean exit and controlled abrupt `_exit(23)`, each repeated with fresh fork/exec peers. Every snapshot, including row padding, matches independent Python byte expectations. The original eight sender-first cases also pass again after the helper change. See [evidence and manifest anchors](../../research/evidence/surface-receiver-2026-10-09.json) and [small native goldens](../../tools/re/fixtures/SurfaceReceiverOracle/manifest.json).

## Measured sequence

The parent creates a surface and one Mach send right. A child obtains the parent's random temporary rendezvous, creates its own receive endpoint, and returns access to that endpoint. Both directions validate kernel audit PIDs against the owned peer before accepting messages. The parent copies the surface send right into the child's endpoint.

The receiver validates geometry, format, identity and its one imported send-right user reference, snapshots the initial pixels, then changes byte zero with XOR `0x5a`.

- **Clean receiver:** explicitly deallocates the imported Mach right, checks that its name has no send-right references, verifies the remaining CF surface alias still exposes the expected bytes, releases the alias and acknowledges completion before normal exit.
- **Abrupt receiver:** acknowledges the completed mutation while both references remain live, then invokes `_exit(23)`. Process teardown owns their cleanup. This is a controlled exit, not an arbitrary crash simulation.

The parent checks the actual wait status, snapshots the receiver mutation after exit, mutates byte one with XOR `0xa6`, and snapshots again. It then drops its original CF surface reference, looks up a new alias through the retained Mach right, checks identity and snapshots the same bytes. Finally it releases that alias and Mach right.

Parent-local send-right user references measure `1 → 1 → 1 → 0` at creation, after copy-send, after receiver exit and after explicit release. These are local right counts, not global kernel object reference counts. The retained-port snapshot demonstrates access after original CF release; it does not prove final memory reclamation.

Successful completion also requires destruction of the temporary rendezvous receive right and bounded lookup returning unknown service. No persistent helper or service is installed. Only the repository-owned peers are launched or terminated.

## Exact-output verification

The adapter checks four stages: initial, after receiver exit, after parent mutation and after original owner CF release through the retained port. Each of the eight cases repeats twice and preserves identical bytes. Metadata, audit-peer flags, distinct process identities, exit status, release path and local right counts must also match; a nonzero helper exit cannot pass based on partial output.

The 3×2 synthetic golden retains 256 bytes per stage, including 128-byte rows. Initial and post-exit bytes exactly match the previous sender-first golden; both final stages match its final mutation golden. The independent system byte comparator confirms all four comparisons with zero differing bits. Tests reject changed padding, absent stages, incorrect counts, wrong release path, wrong exit status, same-process identities and truthy integer attestations.

The controller freezes worker sources and seals artifacts. Published manifest SHA-256 anchors permit comparison against a separately trusted commit or reviewer copy. Sealing verifies consistency; it does not create an independent behavioral oracle. The kernel APIs, known synthetic inputs, separate Python expectations, previous native goldens and system comparator provide different checks within this bounded scope.

## Limits and next experiment

This advances [R1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/5); it does not complete it. Discriminating failure/timeout cleanup controls and final-release reclamation evidence remain missing. Next controls should interrupt handoff before/after import and acknowledgement, account for owned endpoints and rights, and verify that unsuccessful runs cannot promote partial byte checks to success.

Resource reuse, frame generations, stale handles, delayed consumption and completion ordering remain R2 work. GPU synchronization, multiple planes and broader formats remain R3 work. The transport is an owned Mach fixture, not the recovered Canvas XPC envelope. No real Canvas image or portable SwiftUI renderer is claimed. Deprecated bootstrap registration remains a local research dependency and may be unavailable on other OS versions or sandboxes.
