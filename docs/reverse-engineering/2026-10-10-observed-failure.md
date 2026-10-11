# Observer loss: caller settlement and descendant release differ

Two owned controls now discriminate observation failure from output-pressure
cleanup. Their predictions are declared in the frozen control source and the
canonical experiment checks before execution.

In the loss control, a target forks a child which calls `setsid()` and retains
stdout for seven seconds. After its full identity is observed, the fixture
changes only its private helper copy. The supervisor rejects the changed helper
hash and reports `drained=false`. Node kills its inherited group. The escaped
child still owns stdout, so retiring the supervisor alone cannot settle the
caller. At the declared 500ms target budget plus five-second emergency budget,
Node closes its own pipes and rejects the request. The receipt now explicitly
records `emergencyClosed=true`. The child subsequently writes `late`, then exits
through its naturally bounded fixture lifetime. That failure is retained.

Canonical measured settlement was 5,506ms. This is support for bounded caller
settlement and rejection of unknown cleanup. It is a counterexample to treating
closed pipes or supervisor exit as proof that all descendants have released.
The lost observer is not automatically restored, and no stale PID is signalled
without a current full-identity observation.

In the pressure control, the helper stays valid. After the escaping child is
observed, its parent emits 80,001 ASCII bytes against a 1,024-byte capture budget.
Node requests private abort. The supervisor drains matching observed identities
and reports zero remaining live observed processes. The request still rejects
with the output-limit reason. Canonical settlement was 258ms, emergency closure
was false, and the delayed write was absent after the child's natural lifetime.

[Sealed evidence](../../research/evidence/observed-failure-2026-10-10/manifest.json)
retains both outcomes, frozen implementation/control source, and the canonical
fresh-process verification. The independent reader checks every artifact byte,
the actual retained `late` file, capture bounds, rejection reasons, emergency
closure and drain fields. Four resealed false claims for release, marker outcome,
settlement time and oversized captured output reject. Scientific review and
delivery acceptance remain pending.

The canonical live-swap adapter adds three failure checks while keeping all
previous frame, independent/native allocation, fresh compiler, guard, cancellation,
private-input and resource controls. These are owned reconstruction controls;
they do not recover Xcode Canvas release semantics. Unknown escaping descendants
between observations and the observation-to-signal race remain excluded. The
macOS public helper and the offline private Canvas bridge are separate resources.

```sh
research/venv/bin/python tools/re/tests/verify_observed_failure.py research/evidence/observed-failure-2026-10-10
research/venv/bin/python -m unittest discover -s tools/re/tests -p 'test_observed_failure.py'
```

Next: malformed/partial observer results and cancellation at each drain boundary
must reject unknown accounting. Continue native transport work only when its
approved capture prerequisites change.
