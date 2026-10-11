# Missing and empty source restoration in the owned MCP session

The official MCP client 2.3.1 measured one owned handler 0.2.1 server through its
actual stdio transport and the existing wait-recording supervisor. The initial
13×7 source was accepted. Renaming the owned source away made readiness stale
with an unavailable-source diagnostic, while the entire accepted frame remained
available. Repeating the unavailable poll returned identical status. Restoring
exactly the same source produced a new publication. Emptying the source then
made readiness stale with invalid-source, retaining that second publication.
Repeated empty-source polling did not add events. Restoring identical source
again produced a third publication; an unchanged valid poll did not rebuild.

| Source state | Revision | Accepted generation | Readiness | Retained events |
| --- | ---: | ---: | --- | ---: |
| Initial supported source | 1 | 1 | ready | 2 |
| Missing, then repeated missing poll | 1 | 1 | stale | 3 |
| Exact source restored | 2 | 3 | ready | 5 |
| Empty, then repeated empty poll | 2 | 3 | stale | 6 |
| Exact source restored, then unchanged poll | 3 | 5 | ready | 8 |
| Closed | no frame | no frame | closed | 8 |

The competing claim that an equal restored source digest reuses the original
publication without building is contradicted within this owned workflow. Source,
generated module and full allocation digests are identical across all three
accepted frames, but their revision/generation pairs differ. Three distinct
compiler stage directories, successful actual CLI waits and receipts establish
three fresh build invocations. Missing/empty observations do not launch additional
compiler attempts: there are exactly three builds and zero build failures in the
sealed lifecycle. Invalidation consumes generations 2 and 4 without publishing.
Revision identifies an accepted publication; it is not a content digest or proof
of a physically new native surface.

Every byte of six consumer frame allocations was checked independently, totaling
98,304 bytes including row padding and unused tails. Three fresh V8 instances
render the saved modules against the finite Python source expectation. The
pinned official JSON-RPC/initialize/tool-list/tool-result schemas validate all
19 correlated responses. Actual server wait is 0; closure clears availability
and leaves zero owned workers/timers, building and busy. Four resealed faults
reject wrong restored revision, wrong generation, nonzero server wait and a
padding-byte change propagated through retained frames, allocation digests,
status descriptors and correlated wire/partial transcripts. The SDK's 1,108
installed files were rechecked before and after reuse. The isolated candidate
archive passes 93 Python and seven Rust tests.

This extends the scoped reconstruction verification with a repeatable owned
interaction control and independent evidence reader; no runtime policy change
was needed. It does not establish native Canvas refresh, state preservation/reset,
transport ordering, physical reclamation, browser or platform delivery. The
finite source has no user state to migrate; identical image bytes do not prove
state preservation. Native R1/R2 acceptance and both milestones remain open.

Evidence: `research/evidence/mcp-restore-2026-10-11/manifest.json`, SHA-256
`cf0d596d25715639d47eb350a959fea14fe7621f1cb012bc5518152c3c9a42de`.

The initial bridge/GitHub read was not executed because automatic approval review
could not complete while account usage was exhausted. No bypass was attempted.
After the reported reset time passed, the review accepted read-only checks: the
retained approved bridge remains offline/unresponsive and both milestone backlogs
remain open. No bridge restart or user workspace action occurred.

Next: define explicit refresh versus unchanged-poll/reset semantics from separately
scoped owned evidence; do not infer native Canvas state from this finite model.
A native correlated capture still requires restoration of the approved bridge.
