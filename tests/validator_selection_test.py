import unittest

from src.data import load_dataset
from src.validator import Selection, SelectionItem, validate

DATASET = load_dataset()
VALID = Selection((
    SelectionItem("M7", "nura"), SelectionItem("M8", "nura"),
    SelectionItem("M10", "nura"), SelectionItem("M12"),
    SelectionItem("M5", "saryarka"),
))

class ValidatorTests(unittest.TestCase):
    def test_reference_selection_is_valid(self):
        self.assertTrue(validate(VALID, DATASET).valid)

    def test_detects_budget_and_count(self):
        selection = Selection((SelectionItem("M3", "nura"),) * 4)
        reasons = validate(selection, DATASET).reasons
        self.assertTrue(any("ровно 5" in reason for reason in reasons))
        self.assertTrue(any("Повторы" in reason for reason in reasons))
        self.assertTrue(any("бюджет" in reason for reason in reasons))

    def test_detects_targeting_direction_and_incompatibility(self):
        selection = Selection((
            SelectionItem("M1", "nura"), SelectionItem("M3", "esil"),
            SelectionItem("M4", "nura"), SelectionItem("M7", "nura"),
            SelectionItem("M2", "nura"),
        ))
        reasons = validate(selection, DATASET).reasons
        self.assertTrue(any("городской меры" in reason for reason in reasons))
        self.assertTrue(any("направлении" in reason for reason in reasons))
        self.assertTrue(any("M1 и M3" in reason for reason in reasons))
        self.assertTrue(any("M4 и M7" in reason for reason in reasons))

if __name__ == "__main__":
    unittest.main()
