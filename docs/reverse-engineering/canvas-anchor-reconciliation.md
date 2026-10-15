# Repository anchors for two report-only reference gaps

The prior crosswalk found two reports that reference evidence paths without literally stating the computed manifest digest: native State binding and preliminary partial-right failure controls. Their source documents are unchanged. This follow-up adds a separate repository-anchoring record instead of inserting a new digest into the historical text or changing the old document-anchor flags.

The State-binding manifest is present in commit959d7d600eb86d1d4df5a8ad601199c80a19965e with SHA-2567f9ecd5288bd62f5d0f8a2136cebce157b523fcb430a9267c715189b1add172e. The preliminary partial-right manifest is present in commitf60d1ef99f4e07893113a58440d8b337c51f3ce8 with SHA-25625583eef6084ed9e9ef387fab81b794774c1505a04c4966659a2b00b8b59e28e. Both commits are ancestors of the captured published origin/master referencee5f9a769046c6e9f65be40dadf50fd39168f7960.

For both manifests, `git show` bytes match the crosswalk's SHA-256. Git blob identities are independently recomputed from the exact `blob LENGTH\0` prefix and frozen manifest bytes, then compared with the commit tree entries. Frozen references contain repository-authored manifest metadata, not target binaries or private dumps. A separate reader checks those bytes and seven resealed object/trust faults.

This binds repository snapshots, not an independently trusted external authority or the semantics of the experiments. The two original reports still omit a digest. Independent external trust, semantic review, task acceptance and clean-handoff approval remain false. No native process was launched and no product behavior changed. Evidence: `research/evidence/canvas-anchor-reconciliation-2026-10-14`.

The review inputs are now concrete:50 exact-span candidates, ten reports, eleven checked artifact inventories and these two additional repository anchors. More unchanged hashing or ancestry scans would not resolve semantic validity. See the separate-context review brief before choosing another audit.
