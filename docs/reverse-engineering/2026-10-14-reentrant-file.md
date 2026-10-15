# Nested source observations during cancellation

A cooperative builder abort listener can synchronously replace the source file and call poll or refresh. Previously, the outer observation resumed afterward and overwrote the newer pending source. Both retained before controls published source A while source C was on disk, then skipped C on an unchanged poll.

The file loop now gives each accepted observation an identity before invoking cancellation. If a nested observation supersedes it, the outer observation stops before creating a build ticket or overwriting pending work. Poll and forced-refresh controls both publish C after the fix. Each control uses atomic real-file replacements and actual owned prebuilt WASM execution; no compiler invocation is claimed.

Four bounded controls consumed four acquisition slots. All four complete frame allocations match independently pinned expectations: 65,536 bytes including 336 row-padding bytes and 63,744 allocation-tail bytes. Both fixed controls retain the aborted build diagnostic and close with zero workers, timers or pending builds. An independent sealed reader rejects ten resealed faults. Existing file edit/close and short-read controls are rerun against current implementation; historical short-read evidence remains pinned rather than rewritten.

This establishes owned reconstruction observation ordering, not native Canvas refresh, state migration, UI interaction or transport semantics. REA and the private capture bridge remain separate prerequisites; the bridge is absent. Both milestones and issues #15, #19, #22 and #25 remain open.

Evidence: `research/evidence/reentrant-file-observation-2026-10-14`; manifest SHA-256 `13d58a153a91eb02a586ab26eaea26764addfa1c736ef811ba617b82aa72b922`. Next work: select independent eligible research; repeat native Canvas controls only after approved bridge restoration.
