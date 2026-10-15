# Existing reconstruction provenance: mechanical inventory

The Canvas graph's first investigator task now has a concrete internal inventory: `research/canvas-reviews/provenance-inventory.json`. It contains 159 current working-file hashes plus tracked index-blob identities where applicable. Scope covers the Cargo workspace, reusable preview runtime/adapters, examples, README and the four top-level preview/MCP/compiler entrypoints. It is not a whole-repository audit or an approved implementation input.

Initial collection covered155 files. A subsequent entrypoint review found the four top-level wrappers missing from the declared roots. The155-file inventory and its exact producer source remain sealed beside the revised159-file report; no result was silently replaced. This scope correction demonstrates why a successful inventory program does not prove delivery-path completeness.

Every row remains quarantined pending file-specific provenance review. Origin is not established, license is not assessed, and clean-handoff eligibility is false. Zero assets were found inside these declared roots; this says nothing about other repository/evidence paths or future assets. A shared investigation/reconstruction repository is recorded as an exposure condition; that does not establish how each file was derived. Git authorship, a new filename, passing tests or a matching hash cannot independently establish originality.

The tool performs bounded Git reads, includes tracked and untracked declared files, distinguishes index objects from working bytes, refuses symlink/nonregular/oversized file reads and checks file identity/size/time around hashing. It never publishes file contents, changes product behavior, invokes a native renderer or grants clean-room acceptance. The independent reader checks the retained correction and rejects seven resealed false provenance/acceptance claims. Source-tool tests exercise actual temporary Git repositories, untracked assets, symlinks and size limits.

## Next review

1. Review the current entrypoint/Cargo/example scope for additional delivery candidates before claiming complete coverage.
2. For each candidate, record origin evidence, authoring context and relevant target-exposure events, public references, and any license/attribution evidence. Preserve unknowns rather than assigning an optimistic origin.
3. A separate reviewer chooses retain-for-research, exclude-from-handoff, or require fresh implementation. This exposed context must not rewrite production code as a purported clean-room remedy.
4. Review assets and third-party dependencies separately; an empty asset count is not a license inventory.
5. Submit independently reviewed artifact/check records through the Canvas graph only when all acceptance checks pass. The current task remains unaccepted, and no handoff is approved.

Evidence: `research/evidence/provenance-inventory-2026-10-14`. Both milestones stay open. The next wake should review inventory coverage and provenance evidence; it should not repeat an unchanged scan to manufacture progress.
