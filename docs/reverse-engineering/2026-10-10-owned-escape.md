# Observed group escape versus group-only compiler drain

The owned compiler anchor drains inherited process groups. An owned target that
forks a child which calls `setsid()` leaves that scope. Four actual controls and
a fresh frozen-source replay distinguish this exclusion from observed descendant
cleanup using the public macOS libproc observer.

Before target retirement, each fixture waits for a release file. The observer
records the child while its original parent remains alive, including executable
path and microsecond birth time. The target then exits with status 0 or 7. The
child becomes reparented and retains its own process group. Its natural lifetime
is bounded; a delayed write is the discriminating observable.

| Control | Target status | Delayed child write |
| --- | --- | --- |
| Anchored group alone | 0, 7 both preserved | Present in both |
| Previously observed full-identity descendant drain | 0, 7 both preserved | Absent in both |

The group-only outcomes are retained counterexamples to any broader claim of
all-descendant drain. They are expected under the published inherited-group
contract. The observed arms preserve the same full identity after reparenting
and reject any remaining live observed descendant. Three synthetic selector
controls independently change birth seconds, birth microseconds, and executable
path; none permits a signal. These controls do not simulate actual kernel PID
reuse or remove the observation-to-signal race.

The [sealed evidence](../../research/evidence/owned-escape-2026-10-10/manifest.json)
contains frozen source, owned public-helper compilation output, actual receipts,
and a fresh-process replay receipt. The frozen observer is a copy of the existing
working-tree backend, with provenance hashes. This experiment does not publish
the unrelated staged backend changes or integrate detached-child accounting into
the shipped Node compiler runner. Scientific and delivery acceptance stay pending.

The independent reader checks inventory, every byte hash, target status, group
escape, reparenting, delayed-write outcomes, and negative identity controls.
Two tests pass, including five corrupt or resealed false-claim controls:

```sh
research/venv/bin/python tools/re/tests/verify_owned_escape.py research/evidence/owned-escape-2026-10-10
research/venv/bin/python -m unittest discover -s tools/re/tests -p 'test_verify_owned_escape.py'
```

For a bounded native replay, choose a new output folder and retain the repository
controller lock through `RE_PROJECT_ROOT`; do not execute a second writer:

```sh
PYTHONDONTWRITEBYTECODE=1 RE_PROJECT_ROOT="$PWD" research/venv/bin/python research/evidence/owned-escape-2026-10-10/frozen/tools/re/tests/owned_escape_control.py /private/tmp/owned-escape-new-replay
```

Unseen children that escape between observations remain excluded. The next
implementation decision is an explicit observer-backed owned compiler drain
protocol, with sampling limitations stated and failure/abort controls. No owned
model establishes Xcode Canvas release policy. The private Canvas bridge remains
offline; restoring it requires the approved path and an unlocked host.
