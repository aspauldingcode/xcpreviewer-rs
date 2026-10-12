# Reentrant abort callback closure

The cooperative supersession fix introduced an observable close-ordering gap: a builder's synchronous abort listener can call `loop.close()`, which closes the source host, while the observing poll continues into `begin` or `invalidate`. Actual owned controls reproduce `Source host closed` for valid replacement, invalid bytes, deletion and forced refresh even though the intended close eventually drains correctly.

`SourceFileLoop` now rechecks its closed flag immediately after dispatching abort. If the callback closed the loop, observation returns its existing drain promise without further generation mutation or build scheduling. The callback still settles the cooperative builder; close waits for the worker and pump. This targets closure reentry specifically. Arbitrary listener exceptions, recursive refresh callbacks, noncooperative builders and real compiler-tree termination are separate contracts.

Evidence: `research/evidence/abort-close-reentry-2026-10-11`. Eight actual V8/file controls compare the frozen previous implementation with the fixed implementation across four source modes. The prior poll throws `Source host closed`; the fixed poll settles without that error. Each sequence builds only baseline and the delayed candidate, invokes abort once, clears the closed frame, and ends with zero workers/timers, no busy operation and no build in progress. No third generation or replacement build is observed after callback closure.

All eight accepted baseline allocations compare against a hash-pinned independent source-revision golden:131072bytes including672row-padding bytes and127488unused-tail bytes. Thirteen resealed faults reject errors, reentry/build counts, generation, cleanup, padding/tail and scope corruption. The historical supersession test now pins its frozen implementation hash rather than requiring current source equality; immutable evidence is preserved. Existing actual file polling/close controls remain required checks.

This uses pinned prebuilt WASM in Node v24.19.0 with a20second control deadline and16384byte frame allocation. It is an owned consumer lifecycle policy; no fresh compilation, native Canvas cancellation, state migration, platform-wide qualification or private bridge restoration is claimed. Both milestones remain open.

Next: qualify cancellation through an actual owned builder that cooperatively settles with independent timeout/reap accounting; preserve the libproc zombie uncertainty and avoid unchanged retries.
