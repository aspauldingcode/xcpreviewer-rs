# Owned CLI asynchronous shutdown watchdog

The owned preview stdio CLI now keeps a watchdog until channel shutdown settles. At requested channel duration plus1,000ms grace, it retains a best-effort shutdown-timeout.json snapshot, writes a sanitized timeout diagnostic and terminates its own process with exit4. Normal channel completion clears the timer. Cleanup rejection still exits3; successful cleanup exits0. Timeout metadata explicitly says cleanup unknown and preserves the pre-exit state instead of claiming resource release.

## Selection and provenance

The preceding actual CLI cleanup-exit experiment left non-settling close as a demanded isolation unknown. Graph-loop reports no unfinished running wake, one reviewed-binding-required candidate and incomplete milestones. Live GitHub backlog retains MCP/hardening/packaging and native R1/R2/capture. Approved private bridge remains running/responsive false, retained session cb8b4afc-df18-46cd-b895-fc9b6941327f; no restart or Xcode workspace. Prior stdio-exit seal0a9d54ebb8ea115144260e9f2623a6c46c737350c461c231caf31285d4a2ade9 and independent semantic reader were verified. REA is not required for ordinary owned source/process controls.

Actual Node CLI/stdio/channel/session/worker execute. A frozen test-only preloader explicitly supplies the synthetic no-import WASM compiler receipt from prior controls and overrides session.close with an asynchronous promise that never settles. The positive mode uses the real session close. No Rust/source compiler, native oracle, official SDK or user process is involved. Independent Python client owns every Popen child and sends initialization/start/frame before EOF; each packet is bounded3seconds, each child wait5seconds and outer pair12seconds.

## Discrimination and retained failure

Four actual Node producers cover baseline/fixed positive and hung close. Both positive controls complete exit0, preserve complete cleanup and workers0/timers0/frame null. Baseline hung close exceeds5seconds, writes no lifecycle completion/timeout artifact, and requires the independent controller to kill only its own child; real wait reports timeout true/exit-9 and child reaped. This failure is retained with acceptance false.

With requested channel duration500ms, fixed hung close reaches the1,500ms watchdog and exits4 before the same outer5second wait. The retained snapshot still reports worker1/timers2/closedfalse/frame revision1 and cleanup unknown. It is a pre-exit observation, not a post-exit worker count or physical kernel reclamation claim. The independent parent records exit4 without needing its kill fallback and reaps the child. The CLI calls process.exit only on itself, which ends its owned worker threads; it does not target Xcode, simulators or unrelated processes.

## Evidence and checks

Manifest `c778c790193831c25df741f63da0dceb101b0502821f4eaba42faf905adab2e1` seals exact preloader/client, baseline/fixed runtime, actual process IDs/waits, packets, positive lifecycle and fixed timeout artifact/stderr. Separate reader verifies actual0/-9/0/4 outcomes, timeout flags and parent-reaped state, absent baseline completion artifact, unknown fixed cleanup, exact pre-exit lifecycle and consistent frame identity. It compares65,536 independent allocation bytes across four processes: four active0x77 bytes and all other0xc3 including row padding and tail. Eight resealed faults alter outer wait, exit, timeout flag, reaped flag, cleanup unknown, last observed worker, byte4 or final byte16,383; all must reject despite valid hashes. Isolated tests also rerun current CLI exit0/3 behavior and existing channel cleanup/transport controls.

The historical stdio-exit test no longer requires current executable to remain byte-identical to its prior frozen source. Its historical seal/semantic reader remains intact, and its separate actual current-process test verifies exit0/3 compatibility. This removes an obsolete source pin without weakening historical acceptance.

## Practical limits

The watchdog is an event-loop timer, not an external hard real-time monitor. Synchronous main-thread blocking or blocked synchronous filesystem/stderr operations may delay it; independent callers must retain subprocess deadlines. Timeout evidence writes are best effort and do not prevent self-exit if they fail. The measured failure is asynchronous non-settlement with responsive event loop, on existing Node/macOS. No cross-platform, performance, native R1/R2 or Canvas transport acceptance follows. Both milestones remain open. Finite owned cleanup/exit/watchdog contracts are now bounded at their declared scope; next select an independent acceptance gate rather than creating more permutations of completed controls.
