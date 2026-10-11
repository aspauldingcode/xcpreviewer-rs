# Canonical persistent-host graph execution

The `live_swap` adapter accepts no parameters and dispatches only the consolidated
frozen probe. Campaign experiment `primary-live-wasm-swap` predeclares eight
checks. `research/loop/live-swap-runner.json` binds one task to one experiment,
with one round, three minutes and 64 MiB shared artifact budget. The worker has a
120-second deadline and 32 MiB artifact limit. `tools/re/live-swap-loop.py`
inspects that graph by default and executes only with `--execute`.

Actual owned run `20261011T034242Z-primary-live-wasm-swap-6ce0ce0b` used the
explicit public libproc observer already available in the working repository.
The normal controller's default process observer remains unchanged. All eight
checks passed. A fresh verifier process rechecked the seal and declared checks;
a separate full-byte pass compared all 84 saved allocations to independent
expectations and all 80 native-backed allocations to reused public callback
references. The completed task is skipped by the trusted ledger overlay.

Receipt: `research/evidence/live-swap-binding-2026-10-10.json`. Fourteen graph
runner tests, two adapter-boundary tests and the owned timeout test pass.
Scientific delivery review remains pending. This is owned reconstruction policy,
not recovered Xcode Canvas sequencing, new native captures, browser execution,
or general SwiftUI state migration. The retained private bridge is offline and
was not restarted. No Xcode workspace was opened.
