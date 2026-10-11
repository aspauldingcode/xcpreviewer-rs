# Finite source polling requires a regular-file gate

A FIFO at the source pathname blocked the previous synchronous `openSync('r')`.
The Node event loop could not execute the file loop's 500ms lifetime timer. An
external 1.5s deadline killed and reaped only the newly created control process;
the retained stdout contains `entered` and never `settled`. This falsifies a
bounded-input claim for the previous implementation.

The file loop now requires a regular file, opens with `O_NONBLOCK | O_NOFOLLOW`,
and rechecks the opened descriptor with `fstat`. Every successful open closes in
`finally`. The descriptor check handles replacement after the pathname check;
the flags prevent a replaced FIFO from blocking or a replaced symlink from being
followed. Hosts lacking these flags receive an unavailable-source diagnostic.
The contract is owned local POSIX regular files. It does not establish Windows
acceptance or bounds for arbitrary filesystem latency.

Seven actual filesystem controls cover FIFO, directory, symlink, missing source,
regular source, and deterministic FIFO/symlink replacement between `lstat` and
`open`. Replacement controls change real owned fixture nodes before the real
open; they do not fabricate `fstat` results. The FIFO loop closes through its
500ms timer. Invalid inputs invoke no builder. The regular input invokes one
builder. All opened descriptors close; all loop timers and workers reach zero.

[Sealed before/fix evidence](../../research/evidence/source-input-gate-2026-10-10/manifest.json)
includes frozen source, actual receipts, and the first control harness failure:
the new test initially requested `workers` instead of the existing `liveWorkers`
status field. Fixing the test field made no implementation/deadline change.
An independent reader checks hashes and control outcomes. Four resealed false
claims for descriptor release, automatic closure, rejected-input compilation,
and remaining timers fail. Scientific and delivery acceptance remain pending.

The canonical live-swap adapter now executes these controls and declares three
additional checks. Its existing independent/native full-allocation comparisons,
fresh compilation, revision, cancellation, guard and inherited-orphan checks
remain required. This is a reconstruction deadline fix, not evidence of native
Xcode Canvas release policy. The offline private bridge remains a separate gate.

```sh
research/venv/bin/python tools/re/tests/verify_source_input.py research/evidence/source-input-gate-2026-10-10
research/venv/bin/python -m unittest discover -s tools/re/tests -p 'test_source_input_gate.py'
```

Continue the observer-backed owned compiler drain design with the previous
observed-ancestry limitation. This wake addressed an independently discriminated
input/deadline failure before that larger protocol integration.
