# Native cancellation-token copies and owned resource lifetime

Static expansion remains paused. After the UI target/marker failure, this route uses **owned test processes**, not Xcode UI or attachment to the user Xcode process. It converts existing observer/token behavior into native copy/cancel/destruction controls.

## Observed contract on the pinned profile

Two fresh qualified cohorts, B and C, each execute an owned ABI preflight followed by five native token controls. All twelve children exit zero without timeout. B/C use identical native source hashes. The actual shipped PreviewsFoundationHost observer/token methods execute in these helpers, with the existing loaded-path, SHA, UUID `6b75229bde5d3d3794bc75af4f4704c6`, symbol-offset and token-layout guards. Token size/stride is 24; destructor qualification is inherited from the existing observer suite.

| Native control | Actual observations |
| --- | --- |
| Copy then destroy original, invalidate | Original token destruction leaves context/FD live; invalidation calls the observer once and releases/closes the owned context/FD. Remaining copied token can be cancelled/destroyed without another callback. |
| Copy then cancel original | Owned context deinitializes and FD closes during original cancel, while copied token storage remains. Cancel through the copy and later invalidate produce no callback. Both token values destroy cleanly. |
| Destroy both token values while waiting | Context/FD remains live after both value destructions. Invalidation still invokes the observer once, then context/FD cleanup occurs. Dropping values does not cancel this registration. |
| Release owner while both values remain | Actual weak owner and context become nil, FD closes during owner release. Subsequent cancel/destroy of both token values invokes no observer. Copies do not keep this owner alive. |
| Cancel copy and destroy both values during blocked callback | Callback blocks on a semaphore in a raw-context branch. Cancelling the copy and destroying both token values return while context/FD remain live. After unblock/final body marker, context deinit/close occur on the callback worker before invalidate returns; final caller observes nil/EBADF. |

This verifies scoped behavior of copied values addressing the existing registration. It does not identify an internal shared mutable cell, numeric retain counts, arbitrary generic token layout, UI owner identity, renderer/provider/transport settlement, or complete Canvas lifecycle. Positive weak reads are sampled liveness checks; they may temporarily retain the object. The qualified blocked callback does not materialize a strong Probe local; deinit on its worker before join/caller cleanup is asserted. The last callback-body marker is not a separate instruction-level callback return probe.

## Minimum interface qualification, not new static body discovery

To actually copy a token rather than byte-copy an ARC value, the harness uses runtime-published value metadata table slot +16. An owned three-reference/24-byte value first exercises that interface: copying returns destination storage, destroying original storage leaves the owned object/FD live, and destroying the last copy releases/closes it. Only after this owned ABI control passes are the private token controls run. The token copy table entry resolves to PreviewsFoundationHost +0x12a0ec in both cohorts. This is interface qualification needed for the experiment; no new function body, instruction dump or broad symbol inventory is recovered/published.

Original bridge/source files and every child output/status are retained. Native callbacks, weak checks, destructor events, real `close` return zero and `fcntl` EBADF assertions execute; these are not simulated replays. Eight synthetic corruptions exercise the reader only and are separately labelled.

## Preliminary limitation preserved

Preliminary A's six owned children also exit zero, but its blocked callback uses the inherited general callback path, which obtains a strong Probe local. That is a retention confound: the sample cannot isolate native capture retention from callback-local ownership. A's original source/traces stay in preliminary-a/. It is **not** counted as a qualified copied-token in-flight retention result. The callback is then changed to raw-pointer identity plus string/semaphore logging, with no Probe recovery, before fresh B/C. Other A cases remain observations, but final qualified counts use only B/C to keep a consistent source profile. No failing native assertion, crash or unchanged crash retry is hidden by this requalification.

The default Swift compatibility-mode compiler emits WeakMutability warnings and a legacy concurrently executed global-function Sendable warning. Full original diagnostics are retained. These builds pass and execute, but do not establish Swift 6 strict-concurrency correctness or general data-race freedom. The bounded event logger uses a lock; the blocked control has explicit semaphore/join handoffs.

## Reproduction and limits

Follow tools/re/native-canvas-token-copy-runtime/README.md. The outer run stops on owned ABI failure before private token calls; fresh output and native deadlines are mandatory. The runner's kill-on-deadline capability is scoped to its own compiler/helper process groups; no deadline fires in these cohorts. The exclusive controller lock covers each native case. These helpers do not attach to or send input to Xcode/simulator; no stale UI resolver, permission prompt, re-signing or system-protection change is used.

Inspect retained evidence without native execution:

```
python3 tools/re/native-canvas-token-copy-runtime/verify.py research/evidence/canvas-runtime-token-copy-2026-11-03/b
python3 tools/re/native-canvas-token-copy-runtime/verify.py research/evidence/canvas-runtime-token-copy-2026-11-03/c
python3 tools/re/native-canvas-token-copy-runtime/mutations.py
```

Existing user-Xcode crash/changed-target and counter-interaction limitations remain in the previous checkpoint and are not resolved by these component tests. Actual private observer/token and owned-context cleanup is exercised here; full application resource release, rendered/state continuity, cross-platform WASM functionality and milestone target coverage remain unverified. No new Rust/WASM feature or full accepted native area: 0/9 areas; tracked issues 1/26 (3.8%).
