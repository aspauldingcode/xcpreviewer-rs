# Imported Mach-name lifetime versus retained surface aliases

The existing delayed-reuse native fixture now measures immediate IOSurface lookup from imported task-local Mach names at each release boundary. Four shapes × reused/separate surfaces × two repeats produce 16 owned, kernel-audit-verified peer executions; all checks pass.

| Boundary | Reused storage | Separate storage |
| --- | --- | --- |
| After first import right drops | Coalesced name has one send reference and still looks up the same surface | First name no longer looks up; second name still looks up its own surface |
| After second import right drops | Both recorded names return no surface | Both recorded names return no surface |
| Retained first CF alias | Exact generation-two pixels survive | Exact generation-one pixels survive |

Lookups return actual native surface IDs or zero for null; the verifier compares identities and rejects missing values, boolean/integer substitution and wrong outcomes. Lookup calls do not change the measured remaining send-reference count. After both drops, neither imported name has a send reference, but CF aliases still produce exact bytes. The sender retains its own rights until its controlled cleanup.

Eighty snapshot comparisons cover 51,200 bytes against an independent Python expectation, including every row-padding byte and seed wraparound. Both selected delayed snapshots also match prior sealed 256-byte goldens exactly. All 100 tests pass; the verifier rejects altered lookup lifetime evidence while preserving existing metadata, peer, byte, exit and release checks.

This is an immediate owned CPU boundary, not a stale-name security guarantee. No unrelated port allocation is intentionally interposed; arbitrary name recycling remains untested. Failed lookup does not imply memory reclamation: retained aliases and sender rights intentionally keep resources alive. The fixture's generations/acknowledgements do not recover Canvas completion, cancellation, GPU fences or wire semantics. R1/R2 and both milestones remain open.

No Xcode workspace was opened. The planner was separately fixed to recognize verified intentional dark/light/dark blank reversal as resolved contrast diagnosis, while continuing to require live transport evidence. Failed or incomplete scheme controls still request diagnosis.

See [sanitized evidence and trusted anchor](../../research/evidence/surface-retired-name-2026-10-09.json). Run `20261009T163058Z-owned-surface-retired-name-f8c5729c`; manifest SHA-256 `20801a15d227817f3f53744a9a19699a20bcb20c23edb3efa3de21f59dd5eaba`.
