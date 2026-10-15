# Independent documentary query review — 2026-10-15

Reviewer `/root/refresh_spec_review` inspected the read-only query tool, four query tests and saved JSON/Markdown examples. **Approved after one concrete tooling fix.**

Retained failure: two aliases differing only in explicit `target_version` merged into one group before correction (expected 2, observed 1). The current pinned sample contains no such version metadata. The fusion key now includes explicit target version as well as target identity; both are retained in results when present. The existing fusion test now covers differing source paths, target identities and versions in addition to scope, grade and source digest. Tool and test edits held the Controller lock.

Four query tests passed before and after the fix. Eleven additional targeted tamper controls rejected: each pinned artifact's changed bytes, repinned entity/endpoint-review changes, repinned SUPPORTS substitution and four repinned relation-review failures. Distinct scope, grade, source path/hash, target identity and version all remain separate. Saved refresh/release outputs exactly match current results. The JSON retains every control and the original failure.

The loader rechecks exact artifact/review pins, current source hashes/spans, endpoint and edge judgments, ontology and regeneration bindings. Result labels retain documentary ASSERTS, false truth entailment, false native acceptance and false global graph acceptance. No runtime truth or SUPPORTS inference follows. `query(data, ...)` expects the validated loader result; the artifact pins are the trust boundary.

This is a reused ten-report Evidence/Claim development tool, not held-out/global/runtime/native acceptance. The reviewer made the stated repair and does not claim independence from that repair. No product/native/UI/compile, Git, delegation, accepted graph edge, graph fusion write or attestation occurred.

The bounded graph pilot ends here. Native or portable prerequisite work is separate.
