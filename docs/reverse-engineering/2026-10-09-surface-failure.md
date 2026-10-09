# Failed handoff cleanup and surface recycling state

The recurring RE agent implemented and sealed two new controls. Twelve fault cases (four CPU BGRA shapes × three stages) and four use-state cases each repeat with fresh processes. All expected bytes, including padded rows, match independent Python predictions. A final fault campaign repeats successfully against the revised shared helper. All 79 automated tests pass. See [run anchors and checks](../../research/evidence/surface-failure-2026-10-09.json) and [small native goldens](../../tools/re/fixtures/SurfaceFailureOracle/manifest.json).

## Fault stages and cleanup

| Control | Native discriminator | Receiver cleanup | Parent checks |
| --- | --- | --- | --- |
| Before transfer | Receiver destroys endpoint; send returns `MACH_SEND_INVALID_DEST`; peer exits 41 | Explicit endpoint destruction | Sender retains one local surface send reference and exact unchanged pixels |
| After import | Receiver snapshots imported bytes, rejects completion and exits 42 | Explicit imported-right release, remaining CF alias byte check, CF release and endpoint destruction | Audit-verified error acknowledgement, actual exit status, exact unchanged pixels |
| Before completion acknowledgement | Receiver proves import and then withholds completion; 250 ms receive returns `MACH_RCV_TIMED_OUT` | Parent terminates only its owned stalled child; wait confirms SIGKILL | Exact retained pixels; expected completion remains rejected |

All successful fault controls explicitly release the parent's surface reference, Mach resource right and peer endpoint right, require the local resource/endpoint names to disappear, and remove the random temporary rendezvous. The timeout child leaves its imported references to kernel process teardown. This records local right/name accounting and actual child termination; it does not expose global kernel reference counts or allocation reclamation.

The helper returns zero when the expected fault experiment is verified, while its structured result records `completion_accepted: false`. This is experiment success, not successful preview completion. The Python assessor rejects any nonzero helper exit even if success-shaped JSON and correct partial snapshots exist. Tests also reject missing/imported extra stages, wrong error codes, wrong exit/signal, same-peer identity, incorrect retained counts, false cleanup flags and altered padding.

An initial unsealed before-transfer calibration returned helper exit 43. The receiver could close its endpoint before the parent obtained a usable readiness right; this race explanation is inferred from the flow, not a captured wire trace. A new audit-verified parent proceed acknowledgement gates endpoint destruction. The final sealed controls pass. Initial calibration failures remain local and are not promoted into native claims. A schema/executor mismatch found by tests was fixed before publication.

## Recycling state is not memory lifetime

A second native control samples five stages: retained CF surface only, Mach port added, explicit local use incremented, Mach port removed, and explicit local use decremented. For every shape and repeat:

| Observation | CF only | + Mach port | + explicit use | − Mach port | − explicit use |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local explicit use count | 0 | 0 | 1 | 1 | 0 |
| Global in-use predicate | false | true | true | true | false |

The final stage still provides all expected pixels through the retained CF reference. Therefore local explicit count zero does not mean globally unused, and global in-use false does not mean allocation destroyed. The pinned IOSurface SDK contract distinguishes the debugging local count from the global recycling predicate; the evidence records its header hash. Neither API establishes actual Canvas completion ordering or GPU readiness.

Two published 256-byte snapshots—after timeout and globally not-in-use with CF ownership—exactly match the prior native initial golden. Independent system cmp confirms zero differing bits. Frozen worker sources, sealed artifact hashes and externally published manifest anchors retain provenance. Raw Apple binaries, private traces and full SDK headers are not published.

## Remaining work

[R1](https://github.com/aspauldingcode/xcpreviewer-rs/issues/5) remains open for a discriminating final-release reclamation observable and broader failure coverage required by the declared contract. The tested fault stages advance its cleanup requirement without proving every release race.

[R2](https://github.com/aspauldingcode/xcpreviewer-rs/issues/6) remains open: implement separate frame-generation/resource identity, stale handles, delayed consumers and completion ordering. Use-state controls give a reference boundary for recycling; they do not recover Canvas's actual reuse protocol. GPU fences, multi-plane formats, the live Canvas envelope and portable SwiftUI execution remain unverified. Deprecated bootstrap registration remains a local research dependency.
