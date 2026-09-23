import unittest

from src.data import load_dataset
from src.engine import score, score_baseline
from src.validator import Selection, SelectionItem


DATASET = load_dataset()
REFERENCE = Selection((
    SelectionItem("M7", "nura"),
    SelectionItem("M8", "nura"),
    SelectionItem("M10", "nura"),
    SelectionItem("M12"),
    SelectionItem("M5", "saryarka"),
))


class ScoringTests(unittest.TestCase):
    def test_no_action_baseline_matches_source(self):
        result = score_baseline(DATASET)
        self.assertAlmostEqual(result.score, 52.55768, places=5)
        self.assertAlmostEqual(result.score, 52.56, places=2)
        self.assertAlmostEqual(result.d_avg, 56.8624, places=4)
        self.assertAlmostEqual(result.min_district, 49.18, places=2)
        self.assertEqual(result.n_crit, 2)

    def test_reference_set_reproduces_source_example(self):
        result = score(REFERENCE, DATASET)
        self.assertTrue(result.valid)
        self.assertEqual(result.budget_used, 95)
        self.assertAlmostEqual(result.score, 56.54307, places=5)
        self.assertAlmostEqual(result.score_delta, 3.98539, places=5)
        self.assertEqual(result.n_crit, 0)
        synergy = [item for item in result.contributions if item.measure_id == "M10+M12"]
        self.assertEqual(synergy[0].district_id, "nura")
        self.assertEqual(synergy[0].indicator, "B1")
        self.assertEqual(synergy[0].delta, 2.0)

    def test_synergy_is_not_lag_scaled_and_order_does_not_matter(self):
        items = (
            SelectionItem("M1", "nura"), SelectionItem("M2"),
            SelectionItem("M9", "esil"), SelectionItem("M10", "esil"),
            SelectionItem("M12"),
        )
        result = score(Selection(items), DATASET)
        reordered = score(Selection(tuple(reversed(items))), DATASET)
        nura = next(district for district in result.districts if district.district_id == "nura")
        t1 = next(delta for delta in nura.deltas if delta.indicator == "T1")
        self.assertAlmostEqual(t1.after, 64.5)  # 55 + 6*.75 + 4*.75 + 2
        self.assertAlmostEqual(result.score, reordered.score)

    def test_invalid_selection_has_no_score(self):
        result = score(Selection((SelectionItem("M3", "nura"),) * 5), DATASET)
        self.assertFalse(result.valid)
        self.assertIsNone(result.score)
        self.assertTrue(result.validation.reasons)
        self.assertEqual(result.districts, ())


if __name__ == "__main__":
    unittest.main()
