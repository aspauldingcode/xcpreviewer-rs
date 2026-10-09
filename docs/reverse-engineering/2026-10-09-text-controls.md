# Inline text/layout discrimination

Owned inline previews 4–7 isolate plain Text, a default-font stack, title-font Text, and the original stack without its white background. All four return content in sealed run `20261009T155924Z-native-canvas-text-factor-controls-aadb9116`. Interior nonwhite counts are 1,511 / 3,064 / 3,928 / 147,456. Plain text and no-background stack were visually inspected and show their expected labels. The last count includes the entire dark background and is not a glyph count. Nonwhite presence is a sanity check, not OCR or semantic conformance.

These observations rule out blanket text/font failure for the changed inputs. They do not yet establish why the previous custom `ProbeView` snapshots were blank: inline construction, background and styling remain confounded. Next compare structurally identical inline/custom bodies under pinned appearance, then unchanged A/A and controlled label A/B. Full-frame bytes, text recognition, runtime hooks and correlated IPC remain separate gates.

Artifacts and frozen sources verify against the [published anchor](../../research/evidence/canvas-text-controls-2026-10-09.json). [Small owned snapshots](../../tools/re/fixtures/CanvasTextOracle/manifest.json) preserve the observed outputs. Existing 94-test baseline remains; six targeted capture/ownership guard tests pass after this fixture change. Native build and four render calls also pass.

The experiment's owned workspace was closed through verified UI state immediately after completion. Read-only window listing confirms no workspace windows remain. The welcome-window close attempt was not confirmed; no additional project was opened. Xcode and retained broker were preserved. O2/O3 and both milestones remain open.
