import unittest

from src.app import format_catalogue, format_result, parse_selection_item, selection_from_inputs
from src.data import load_dataset
from src.engine import score


class CliTests(unittest.TestCase):
    def setUp(self):
        self.dataset = load_dataset()

    def test_parses_city_and_district_notation(self):
        self.assertEqual(parse_selection_item("m7: NURA").measure_id, "M7")
        self.assertEqual(parse_selection_item("m7: NURA").district, "nura")
        self.assertEqual(parse_selection_item("M12").district, None)
        with self.assertRaises(ValueError):
            parse_selection_item("M7:nura:extra")

    def test_catalogue_comes_from_dataset(self):
        catalogue = format_catalogue(self.dataset)
        self.assertIn("M1", catalogue)
        self.assertIn("Выделенные полосы", catalogue)
        self.assertIn("nura (Нура)", catalogue)

    def test_result_renders_engine_output_and_validation_errors(self):
        selected = selection_from_inputs(["M7:nura", "M8:nura", "M10:nura", "M12", "M5:saryarka"])
        rendered = format_result(score(selected, self.dataset))
        self.assertIn("95/100", rendered)
        self.assertIn("56.54", rendered)
        self.assertIn("Нура", rendered)

        invalid = format_result(score(selection_from_inputs(["M3:nura"] * 5), self.dataset))
        self.assertIn("Набор не принят", invalid)
        self.assertIn("Повторы", invalid)


if __name__ == "__main__":
    unittest.main()
