"""JSON-facing adapters over the simulator's canonical domain modules."""
from __future__ import annotations

from typing import Any, Mapping

from src.ai import explain
from src.data import Dataset
from src.engine import score
from src.validator import Selection, SelectionItem


def catalogue_payload(dataset: Dataset) -> dict[str, Any]:
    """Expose catalogue facts for a browser without copying source data."""
    return {
        "budget": dataset.rules["budget"],
        "required_decisions": dataset.rules["required_decisions"],
        "districts": [
            {"id": district.id, "name": district.name}
            for district in dataset.districts
        ],
        "measures": [
            {
                "id": measure.id,
                "name": measure.name,
                "direction": measure.direction,
                "type": measure.type,
                "cost": measure.cost,
                "lag": measure.lag,
                "effects": dict(measure.effects),
            }
            for measure in dataset.measures
        ],
    }


def score_payload(payload: Mapping[str, Any], dataset: Dataset) -> dict[str, Any]:
    """Score a browser request with existing validation and engine logic only."""
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Поле items должно быть массивом решений.")
    items: list[SelectionItem] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, Mapping):
            raise ValueError("Каждое решение должно быть объектом.")
        measure_id = raw_item.get("measure_id")
        district = raw_item.get("district")
        if not isinstance(measure_id, str):
            raise ValueError("У решения нужен строковый measure_id.")
        if district is not None and not isinstance(district, str):
            raise ValueError("district должен быть строкой или null.")
        items.append(SelectionItem(measure_id.upper(), district.lower() if district else None))

    result = score(Selection(tuple(items)), dataset)
    response: dict[str, Any] = {
        "valid": result.valid,
        "reasons": list(result.validation.reasons),
        "budget_used": result.budget_used,
        "cost_total": result.cost_total,
        "narrative": explain(result),
    }
    if not result.valid:
        return response
    response.update({
        "score": result.score,
        "score_delta": result.score_delta,
        "d_avg": result.d_avg,
        "min_district": result.min_district,
        "n_crit": result.n_crit,
        "districts": [
            {
                "id": district.district_id,
                "name": district.district_name,
                "before": district.before,
                "after": district.after,
                "indicators": [
                    {"id": delta.indicator, "before": delta.before, "after": delta.after,
                     "delta": delta.delta}
                    for delta in district.deltas
                ],
                "changes": [
                    {"indicator": delta.indicator, "delta": delta.delta}
                    for delta in district.deltas if delta.delta
                ],
            }
            for district in result.districts
        ],
    })
    return response
