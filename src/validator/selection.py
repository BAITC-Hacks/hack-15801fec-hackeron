"""Pure validation of a five-decision simulator selection."""
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.data import Dataset

@dataclass(frozen=True)
class SelectionItem:
    measure_id: str
    district: str | None = None

@dataclass(frozen=True)
class Selection:
    items: tuple[SelectionItem, ...]

@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reasons: tuple[str, ...]

def validate(selection: Selection, dataset: "Dataset") -> ValidationResult:
    """Return every violated source rule; selection order has no semantic effect."""
    reasons: list[str] = []
    measures = {measure.id: measure for measure in dataset.measures}
    district_ids = {district.id for district in dataset.districts}
    items = selection.items
    if len(items) != int(dataset.rules["required_decisions"]):
        reasons.append("Нужно выбрать ровно 5 решений.")
    ids = [item.measure_id for item in items]
    if len(set(ids)) != len(ids):
        reasons.append("Повторы мероприятий запрещены.")
    unknown = [item.measure_id for item in items if item.measure_id not in measures]
    if unknown:
        reasons.append(f"Неизвестное мероприятие: {unknown[0]}.")
    cost = sum(measures[item.measure_id].cost for item in items if item.measure_id in measures)
    if cost > int(dataset.rules["budget"]):
        reasons.append("Превышен бюджет 100.")
    directions: dict[str, int] = {}
    for item in items:
        measure = measures.get(item.measure_id)
        if not measure:
            continue
        directions[measure.direction] = directions.get(measure.direction, 0) + 1
        if measure.type == "district":
            if item.district not in district_ids:
                reasons.append(f"Для {measure.id} нужен допустимый район.")
        elif item.district is not None:
            reasons.append(f"Для городской меры {measure.id} район не указывается.")
    if any(count > 2 for count in directions.values()):
        reasons.append("В одном направлении может быть не более 2 мер.")
    by_id = {item.measure_id: item for item in items}
    for rule in dataset.rules["incompatibilities"]:
        first, second = rule["measures"]
        if first not in by_id or second not in by_id:
            continue
        if rule["scope"] == "global" or by_id[first].district == by_id[second].district:
            reasons.append(f"Несовместимы {first} и {second}.")
    return ValidationResult(not reasons, tuple(reasons))
