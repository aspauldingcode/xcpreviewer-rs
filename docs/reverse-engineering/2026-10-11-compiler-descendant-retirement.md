# Explicit compiler descendant retirement admission

An explicit observer could report a child while the root was running, omit that child in its final snapshot, and obtain successful admission. The old predicate examined only known identities still present in the returned rows. Missing rows therefore acted as implicit retirement evidence even though a callback might simply return an incomplete snapshot.

`CompilerWitness.admit` now rejects any missing known non-root identity with `Compiler descendant retirement was not observed`. Matching observed zombie rows can satisfy this narrow CPU-process retirement policy; matching live rows and changed birth identities still reject. The root itself may be absent after the caller has waited for its exit. The optional observer remains explicit; the default compiler path is unchanged.

This conservative policy can reject a legitimately reaped child whose row is no longer available. That is deliberate ambiguity handling, not proof that the child remains alive. A future richer backend may supply independently justified absence/liveness evidence. This implementation neither fabricates absent rows nor silently retries observations. No new signal, native delay, backend launch, or private capture operation is added.

Evidence: `research/evidence/compiler-descendant-retirement-2026-10-11`. Twelve deterministic source controls distinguish omitted, unrelated-only, matching-zombie, live, changed-birth and childless final snapshots before/after. An independent reader rejects eight resealed faults. Tests replay frozen before/after source, require every known child, and drive the real compiler wrapper with a fake process to verify rejection after root success without a cleanup signal. These are source/model controls: no native producer or signal was executed.

Historical active-root and ready-gated native checkpoints remain immutable and hash-pinned. Generic native startup, real LLVM observer admission, native final-zombie qualification, reliable absence after reaping, missed descendants, physical resource reclamation, and Canvas lifecycle/transport remain open. Zombie state is process execution retirement, not IOSurface/GPU reclaim or Canvas completion. Both milestones remain open.

Next: qualify an owned child with an observed matching zombie before reaping under a bounded ready protocol, then assess a separate typed absence contract. Do not reuse source controls as native acceptance evidence.
