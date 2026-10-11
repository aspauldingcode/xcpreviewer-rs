# Explicit observed compiler drain

The optional compiler path now combines a retained inherited-group anchor with
explicit public macOS process observation. Callers supply the owned helper path
and its SHA256; neither observer selection nor an Apple dependency is implicit.
The existing inherited-group path remains the default.

The supervisor samples only its newly created target ancestry and previously
observed full birth/executable identities. A private control pipe carries abort
requests. After completion, timeout or abort, the supervisor signals only matching
observed identities, rechecks for live observed processes, and reports the actual
target wait status. Node then kills the still-live inherited group. The helper is
hashed before and after each bounded call. Process counts, output, reports,
snapshot duration and overall supervisor lifetime are capped. Emergency group
termination rejects cleanup acceptance and closes owned pipes to bound settlement.

Four actual controls create children which call `setsid()`. A private observation
event confirms the child before the fixture releases its parent or requests an
abort. The child retains its observed identity after escape. Success/failure
preserve target status 0/7. Deadline/abort preserve actual target status -15 and
their respective failure reasons. Every case reports zero remaining live
observed processes and has no delayed write after the child's natural lifetime.
A pre-aborted request spawns no target.

Three real frozen-CLI builds use this optional path through the existing source
file loop. Their complete allocations match the separately pinned source/native
reference fixture: 49,152 bytes, including padding and tail. There are no cache
hits. The independent reader rehashes all evidence, including nested compiler
manifests, checks the control/wait receipts, revalidates reference hashes and
compares every allocation byte. Four resealed false claims for drain, remaining
processes, status and allocation tail fail.

[Sealed evidence](../../research/evidence/observed-compiler-2026-10-10/manifest.json)
includes retained setup failure, frozen implementation and actual controls/builds.
The first attempt used a generic reader for a list manifest on a map manifest;
it failed before native execution. A format-specific reader fixed that setup.
The public helper source is reused from the previously sealed owned escape
control. No unrelated staged backend changes are committed.

The canonical live-swap graph now requires four additional checks and executes
both inherited-group and observed paths. Scientific/delivery review remains
pending. Sampling cannot account for unseen children escaping between snapshots.
Full equality before signalling does not eliminate the observation-to-signal
race. Unknown helper failures cannot establish complete cleanup. These owned
controls do not recover Xcode Canvas release policy or satisfy cross-platform
acceptance; the explicit observer path currently requires macOS.

```sh
research/venv/bin/python tools/re/tests/verify_observed_compiler.py research/evidence/observed-compiler-2026-10-10
research/venv/bin/python -m unittest discover -s tools/re/tests -p 'test_observed_compiler.py'
```

Next: falsify observer loss and output-pressure settlement with owned controls;
reject unknown cleanup instead of counting it as release. Native correlated
Canvas capture still requires restoration of the approved private bridge.
