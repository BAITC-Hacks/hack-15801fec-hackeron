"""JSON-facing adapters over the simulator's canonical domain modules."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from src.ai import explain
from src.data import Dataset, District
from src.engine import score
from src.validator import Selection, SelectionItem

RISK_EVENTS: dict[str, dict[str, Any]] = {
    "none": {"name": "Без дополнительного события", "effects": {}},
    "smog": {"name": "Сильный смог в Сарыарке", "effects": {"saryarka": {"E2": -12}}},
    "network": {"name": "Авария ЖКХ в Алматы", "effects": {"almaty": {"C1": -12}}},
    "congestion": {"name": "Рост пробок в Есиле", "effects": {"esil": {"T1": -10}}},
}

def catalogue_payload(dataset: Dataset) -> dict[str, Any]:
    return {
        "budget": dataset.rules["budget"],
        "required_decisions": dataset.rules["required_decisions"],
        "districts": [{"id": d.id, "name": d.name} for d in dataset.districts],
        "events": [{"id": event_id, "name": event["name"]} for event_id, event in RISK_EVENTS.items()],
        "measures": [{"id": m.id, "name": m.name, "direction": m.direction, "type": m.type,
                      "cost": m.cost, "lag": m.lag, "effects": dict(m.effects)}
                     for m in dataset.measures],
    }

def score_payload(payload: Mapping[str, Any], dataset: Dataset) -> dict[str, Any]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Поле items должно быть массивом решений.")
    event_id = payload.get("event", "none")
    if not isinstance(event_id, str) or event_id not in RISK_EVENTS:
        raise ValueError("Неизвестное событие риска.")
    items = _items(raw_items)
    event_dataset = _dataset_for_event(dataset, event_id)
    result = score(Selection(tuple(items)), event_dataset)
    response: dict[str, Any] = {
        "valid": result.valid, "reasons": list(result.validation.reasons),
        "budget_used": result.budget_used, "cost_total": result.cost_total,
        "narrative": explain(result), "event": {"id": event_id, "name": RISK_EVENTS[event_id]["name"]},
    }
    if not result.valid:
        return response
    response.update({
        "score": result.score, "score_delta": result.score_delta, "d_avg": result.d_avg,
        "min_district": result.min_district, "n_crit": result.n_crit,
        "districts": [{"id": d.district_id, "name": d.district_name, "before": d.before, "after": d.after,
                       "indicators": [{"id": x.indicator, "before": x.before, "after": x.after, "delta": x.delta}
                                      for x in d.deltas],
                       "changes": [{"indicator": x.indicator, "delta": x.delta} for x in d.deltas if x.delta]}
                      for d in result.districts],
        "recommendations": _recommend(items, event_dataset, result.score),
    })
    return response

def _items(raw_items: list[Any]) -> list[SelectionItem]:
    items: list[SelectionItem] = []
    for raw in raw_items:
        if not isinstance(raw, Mapping):
            raise ValueError("Каждое решение должно быть объектом.")
        measure_id, district = raw.get("measure_id"), raw.get("district")
        if not isinstance(measure_id, str):
            raise ValueError("У решения нужен строковый measure_id.")
        if district is not None and not isinstance(district, str):
            raise ValueError("district должен быть строкой или null.")
        items.append(SelectionItem(measure_id.upper(), district.lower() if district else None))
    return items

def _dataset_for_event(dataset: Dataset, event_id: str) -> Dataset:
    effects = RISK_EVENTS[event_id]["effects"]
    districts = []
    for district in dataset.districts:
        indicators = dict(district.indicators)
        for indicator, delta in effects.get(district.id, {}).items():
            indicators[indicator] = max(0, min(100, indicators[indicator] + delta))
        districts.append(replace(district, indicators=indicators))
    return replace(dataset, districts=tuple(districts))

def _recommend(items: list[SelectionItem], dataset: Dataset, current_score: float) -> list[dict[str, Any]]:
    """Find small one-measure substitutions that improve the current valid scenario."""
    selected = {item.measure_id for item in items}
    candidates: list[tuple[float, Selection]] = []
    for index in range(len(items)):
        for measure in dataset.measures:
            if measure.id in selected and measure.id != items[index].measure_id:
                continue
            targets = (None,) if measure.type == "city" else tuple(d.id for d in dataset.districts)
            for district in targets:
                replacement = items.copy()
                replacement[index] = SelectionItem(measure.id, district)
                result = score(Selection(tuple(replacement)), dataset)
                if result.valid and result.score is not None and result.score > current_score + 0.001:
                    candidates.append((result.score, Selection(tuple(replacement))))
    candidates.sort(key=lambda item: -item[0])
    unique: set[tuple[tuple[str, str | None], ...]] = set()
    output = []
    for value, selection in candidates:
        key = tuple((item.measure_id, item.district) for item in selection.items)
        if key in unique:
            continue
        unique.add(key)
        output.append({"score": value, "items": [{"measure_id": item.measure_id, "district": item.district} for item in selection.items]})
        if len(output) == 3:
            break
    return output
