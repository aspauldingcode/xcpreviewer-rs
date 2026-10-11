# Structural Canvas diagnostic reader

Four adversarial controls were predicted before execution against the sealed
owned UI diagnostics. The previous descendant-regex reader accepted three
unsupported reports: a renamed `canvasContent` container, a renamed `states`
container, and a missing provider. Each retained a success-shaped result despite
losing the required structural evidence. The fourth added section was rejected.
The previous claim of fail-closed structural reading was therefore too broad;
these failures remain in `before-fix.json` rather than being erased.

The reader now constructs bounded blocks and requires the measured exact path
registry → named preview → canvasContent → states. Provider and registry identities
must match exactly, duplicate fields are rejected, and provider status remains
separate from registry live success. Unsupported state values and report shapes
fail explicitly; this version supports the observed single-content shape only.
Limits are 64 KiB, 2048 lines, 16 nested blocks and 32 registries. No fallback
searches descendants for success labels. Output schema version 2 adds provider
line/status provenance while preserving every measured version 1 field.

Six targeted tests pass, including eleven structural controls, prior corruption
controls, explicit resource bounds, separate provider status and static-only
success. All four retained controls reject after the fix. A separate verification
process rehashed all sealed artifacts, counted the three original false
acceptances/four final rejections, and compared every prior measured output field
except the declared schema version. This is deterministic parser verification;
scientific delivery review remains pending.

Evidence: `research/evidence/canvas-diagnostic-structure-2026-10-10/manifest.json`.
No new owned UI session was opened and no native protocol observation is claimed.
The retained private capture bridge is still offline; its explicit restoration
prerequisite remains unchanged. Both milestones remain open. Next native work
requires attributed interaction input or exported/display color controls; the
graph's portable live-swap candidate still requires a reviewed execution binding.
