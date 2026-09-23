"""Enumerate and rank valid simulator scenarios using the canonical validator/engine."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import TYPE_CHECKING, Iterator

from src.engine import ScoreResult, score, score_value
from src.validator import Selection, SelectionItem, validate

if TYPE_CHECKING:
    from src.data import Dataset, Measure


@dataclass(frozen=True)
class RankedScenario:
    """One valid decision set and its canonical deterministic result."""

    selection: Selection
    result: ScoreResult


def iter_valid_selections(dataset: "Dataset") -> Iterator[Selection]:
    """Yield every valid five-measure selection in stable catalogue order.

    The small structural checks only prune target-independent impossibilities. The
    shared validator remains the authority for every emitted selection, including
    targeting and same-district incompatibilities.
    """
    required = int(dataset.rules["required_decisions"])
    district_ids = tuple(district.id for district in dataset.districts)
    for measures in combinations(dataset.measures, required):
        if not _measure_set_can_be_valid(measures, dataset):
            continue
        target_options = [
            district_ids if measure.type == "district" else (None,)
            for measure in measures
        ]
        for targets in product(*target_options):
            selection = Selection(tuple(
                SelectionItem(measure.id, district_id)
                for measure, district_id in zip(measures, targets)
            ))
            if validate(selection, dataset).valid:
                yield selection


def rank_scenarios(dataset: "Dataset", limit: int = 10) -> tuple[RankedScenario, ...]:
    """Score every valid scenario and return the best ``limit`` in stable order."""
    if limit < 0:
        raise ValueError("limit must be non-negative")
    if limit == 0:
        return ()
    best: list[tuple[float, tuple[tuple[str, str], ...], Selection]] = []
    for selection in iter_valid_selections(dataset):
        value = score_value(selection, dataset)
        candidate = (value, _selection_key(selection), selection)
        if len(best) < limit or value > best[-1][0] or (
            value == best[-1][0] and candidate[1] < best[-1][1]
        ):
            best.append(candidate)
            best.sort(key=lambda item: (-item[0], item[1]))
            del best[limit:]
    return tuple(RankedScenario(selection, score(selection, dataset)) for _, _, selection in best)


def _measure_set_can_be_valid(measures: tuple["Measure", ...], dataset: "Dataset") -> bool:
    """Cheap pruning of constraints which do not depend on district targets."""
    if sum(measure.cost for measure in measures) > int(dataset.rules["budget"]):
        return False
    directions: dict[str, int] = {}
    ids = {measure.id for measure in measures}
    for measure in measures:
        directions[measure.direction] = directions.get(measure.direction, 0) + 1
    if any(count > 2 for count in directions.values()):
        return False
    return not any(
        rule["scope"] == "global" and set(rule["measures"]).issubset(ids)
        for rule in dataset.rules["incompatibilities"]
    )


def _selection_key(selection: Selection) -> tuple[tuple[str, str], ...]:
    return tuple((item.measure_id, item.district or "") for item in selection.items)
