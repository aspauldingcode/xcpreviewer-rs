import unittest
from pathlib import Path
from reloop.canvasdiagnostics import parse_display_state


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "research/evidence/canvas-input-2026-10-10"


class CanvasDiagnosticTests(unittest.TestCase):
    def test_selection_changes_fresh_registry_without_build_completion(self):
        before = parse_display_state((EVIDENCE / "primary-display-state.txt").read_text())
        after = parse_display_state((EVIDENCE / "interaction-display-state.txt").read_text())
        for report in (before, after):
            self.assertEqual(report["building_state"], "Running")
            self.assertFalse(report["is_update_in_progress"])
            self.assertFalse(report["transport_observed"])
            self.assertEqual(len(report["registries"]), 3)
        self.assertEqual([r["reports_fresh_live_success"] for r in before["registries"]], [True, False, False])
        self.assertEqual([r["reports_fresh_live_success"] for r in after["registries"]], [False, True, False])
        self.assertGreater(after["update_identifier"], before["update_identifier"])

    def test_fail_closed_on_corruption_or_ambiguity(self):
        text = (EVIDENCE / "primary-display-state.txt").read_text()
        for damaged in (text[:-3], text.replace("isStale: false", "isStale: unknown"),
                        text.replace("isUpdateInProgress: false", "isUpdateInProgress: false\nisUpdateInProgress: false"),
                        text.replace("#2[preview]", "#1[preview]"), "x" * 65537):
            with self.subTest(damaged=damaged[:60]):
                with self.assertRaises(ValueError):
                    parse_display_state(damaged)

    def test_available_and_static_success_do_not_imply_live_success(self):
        text = (EVIDENCE / "primary-display-state.txt").read_text().replace("livePreview: succeeded", "livePreview: disabled").replace("staticPreview: disabled", "staticPreview: succeeded")
        self.assertFalse(any(r["reports_fresh_live_success"] for r in parse_display_state(text)["registries"]))
