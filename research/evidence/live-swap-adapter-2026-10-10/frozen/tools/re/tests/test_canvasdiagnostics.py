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

    def test_required_structural_path_and_provider_coverage(self):
        text = (EVIDENCE / "primary-display-state.txt").read_text()
        controls = [
            text.replace("canvasContent {", "unrelatedContainer {", 1),
            text.replace("states {", "unrelatedStates {", 1),
            text.replace("Registry[Registry-PreviewLab.swift#1[preview] (line 27)] {\n            status: Completed: Not attempted\n        }", ""),
            text.replace("(line 27)", "(line unknown)"),
            text.replace("providers [", "providers {", 1).replace("    ]\n    registries", "    }\n    registries", 1),
            text.replace("isStale: false", "extra {\n isStale: false\n }", 1),
            text.replace("livePreview: succeeded", "nested {\n livePreview: succeeded\n }", 1),
            text.replace("Light Appearance: disabled", "Light Appearance: unknown", 1),
            text + "\nunsupported {\n arbitrary: true\n}\n",
            text.replace("updateIdentifier: 10543", "updateIdentifier: " + "1" * 21),
            text.replace("states {", "states [", 1),
        ]
        for damaged in controls:
            with self.subTest(damaged=damaged[:100]):
                with self.assertRaises(ValueError):
                    parse_display_state(damaged)

    def test_provider_status_is_separate_from_registry_success(self):
        report = parse_display_state((EVIDENCE / "primary-display-state.txt").read_text())
        self.assertEqual([p["status"] for p in report["providers"]], ["Completed: Not attempted"] * 3)
        self.assertEqual({p["id"] for p in report["providers"]}, {r["id"] for r in report["registries"]})
        self.assertTrue(report["registries"][0]["reports_fresh_live_success"])

    def test_explicit_resource_bounds(self):
        for text in ("\n" * 2049, "a {\n" * 18 + "}\n" * 18):
            with self.assertRaises(ValueError):
                parse_display_state(text)
