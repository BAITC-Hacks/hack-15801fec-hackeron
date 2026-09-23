import unittest

from src.data import load_dataset
from src.web.api import catalogue_payload, score_payload


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.dataset = load_dataset()

    def test_catalogue_reflects_loaded_data(self):
        catalogue = catalogue_payload(self.dataset)
        self.assertEqual(catalogue["budget"], 100)
        self.assertEqual(len(catalogue["measures"]), 14)
        self.assertEqual(catalogue["districts"][-1], {"id": "nura", "name": "Нура"})

    def test_scores_valid_browser_payload(self):
        payload = {"items": [
            {"measure_id": "M7", "district": "nura"},
            {"measure_id": "M8", "district": "nura"},
            {"measure_id": "M10", "district": "nura"},
            {"measure_id": "M12", "district": None},
            {"measure_id": "M5", "district": "saryarka"},
        ]}
        response = score_payload(payload, self.dataset)
        self.assertTrue(response["valid"])
        self.assertAlmostEqual(response["score"], 56.54307, places=5)
        self.assertIn("Итог сценария", response["narrative"])
        self.assertEqual(len(response["districts"]), 5)
        self.assertEqual(len(response["districts"][0]["indicators"]), 10)
        self.assertEqual(response["districts"][0]["indicators"][0]["id"], "T1")

    def test_returns_validation_reasons_and_rejects_bad_shapes(self):
        response = score_payload({"items": []}, self.dataset)
        self.assertFalse(response["valid"])
        self.assertTrue(response["reasons"])
        with self.assertRaises(ValueError):
            score_payload({"items": "M7:nura"}, self.dataset)
        with self.assertRaises(ValueError):
            score_payload({"items": [{"measure_id": 7}]}, self.dataset)


if __name__ == "__main__":
    unittest.main()
