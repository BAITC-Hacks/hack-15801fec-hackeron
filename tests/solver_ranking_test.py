import itertools
import unittest

from src.data import load_dataset
from src.solver import iter_valid_selections, rank_scenarios
from src.validator import validate


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.dataset = load_dataset()

    def test_generated_selections_are_valid_and_stable(self):
        first = list(itertools.islice(iter_valid_selections(self.dataset), 10))
        repeated = list(itertools.islice(iter_valid_selections(self.dataset), 10))
        self.assertEqual(first, repeated)
        self.assertEqual(len(first), 10)
        self.assertTrue(all(validate(selection, self.dataset).valid for selection in first))

    def test_zero_limit_skips_exhaustive_ranking(self):
        self.assertEqual(rank_scenarios(self.dataset, 0), ())
        with self.assertRaises(ValueError):
            rank_scenarios(self.dataset, -1)


if __name__ == "__main__":
    unittest.main()
