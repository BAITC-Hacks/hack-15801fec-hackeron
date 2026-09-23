import unittest

from src.ai import build_prompt, explain
from src.data import load_dataset
from src.engine import score
from src.validator import Selection, SelectionItem


DATASET = load_dataset()
VALID = Selection((
    SelectionItem("M7", "nura"), SelectionItem("M8", "nura"),
    SelectionItem("M10", "nura"), SelectionItem("M12"),
    SelectionItem("M5", "saryarka"),
))


class ExplanationTests(unittest.TestCase):
    def test_prompt_contains_precomputed_audit_facts_and_question(self):
        prompt = build_prompt(score(VALID, DATASET), "Какие риски?")
        self.assertIn("56.54", prompt)
        self.assertIn("M10+M12", prompt)
        self.assertIn("S1 +10.00", prompt)
        self.assertIn("Какие риски?", prompt)
        self.assertIn("Не считай", prompt)

    def test_injected_model_receives_prompt(self):
        received = []

        def fake_model(prompt):
            received.append(prompt)
            return "Ответ модели"

        self.assertEqual(explain(score(VALID, DATASET), model=fake_model), "Ответ модели")
        self.assertIn("ФАКТЫ ИЗ ДЕТЕРМИНИРОВАННОГО РАСЧЁТА", received[0])

    def test_local_fallback_quotes_result_and_handles_invalid_selection(self):
        narrative = explain(score(VALID, DATASET))
        self.assertIn("56.54", narrative)
        self.assertIn("Нура", narrative)
        invalid = score(Selection((SelectionItem("M3", "nura"),) * 5), DATASET)
        self.assertIn("Сценарий не принят", explain(invalid))
        self.assertIn("Score не рассчитан", build_prompt(invalid))


if __name__ == "__main__":
    unittest.main()
