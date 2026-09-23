"""Russian terminal interface for the five-decision city simulator."""
from __future__ import annotations

from collections.abc import Iterable

from src.ai import explain
from src.data import Dataset, load_dataset
from src.engine import ScoreResult, score
from src.validator import Selection, SelectionItem


def parse_selection_item(value: str) -> SelectionItem:
    """Parse ``M7:nura`` (district measure) or ``M12`` (city measure) input."""
    parts = [part.strip() for part in value.split(":")]
    if len(parts) not in (1, 2) or not parts[0] or (len(parts) == 2 and not parts[1]):
        raise ValueError("Формат: M7:nura для района или M12 для городской меры.")
    return SelectionItem(
        measure_id=parts[0].upper(),
        district=None if len(parts) == 1 else parts[1].lower(),
    )


def selection_from_inputs(values: Iterable[str]) -> Selection:
    """Make a selection from terminal-style values without any business validation."""
    return Selection(tuple(parse_selection_item(value) for value in values))


def format_catalogue(dataset: Dataset) -> str:
    """Render source catalogue facts without maintaining a second copy of the data."""
    lines = ["\nКАТАЛОГ МЕР", "ID   Направление    Тип     Цена  Лаг  Эффекты"]
    for measure in dataset.measures:
        effects = ", ".join(f"{name} {delta:+g}" for name, delta in measure.effects.items())
        kind = "район" if measure.type == "district" else "город"
        lines.append(
            f"{measure.id:<4} {measure.direction:<14} {kind:<7} {measure.cost:>3}  "
            f"{measure.lag:>2}   {effects}\n     {measure.name}"
        )
    lines.append("Районы: " + ", ".join(f"{district.id} ({district.name})" for district in dataset.districts))
    return "\n".join(lines)


def format_result(result: ScoreResult) -> str:
    """Render computed values; all arithmetic remains in ``src.engine``."""
    if not result.valid:
        reasons = "\n".join(f"• {reason}" for reason in result.validation.reasons)
        return f"\nНабор не принят. Исправьте:\n{reasons}"

    lines = [
        "\nРЕЗУЛЬТАТ СЦЕНАРИЯ",
        f"Бюджет: {result.budget_used}/100",
        f"Astana Quality of Life Score: {result.score:.2f} ({result.score_delta:+.2f} к базе)",
        f"Среднее по городу: {result.d_avg:.2f}; слабейший район: {result.min_district:.2f}; "
        f"критических значений: {result.n_crit}",
        "\nРайоны:",
    ]
    for district in result.districts:
        changed = [delta for delta in district.deltas if delta.delta]
        changes = ", ".join(f"{delta.indicator} {delta.delta:+.2f}" for delta in changed) or "без изменений"
        lines.append(
            f"• {district.district_name}: {district.before:.2f} → {district.after:.2f} ({changes})"
        )
    return "\n".join(lines)


def main() -> None:
    dataset = load_dataset()
    measures = {measure.id: measure for measure in dataset.measures}
    print("Аким на 5 часов — симулятор решений")
    print("Выберите ровно 5 мер. Формат: M7:nura для районной меры, M12 для городской.")
    print(format_catalogue(dataset))

    raw_items: list[str] = []
    while len(raw_items) < int(dataset.rules["required_decisions"]):
        position = len(raw_items) + 1
        raw = input(f"\nРешение {position}/5: ").strip()
        try:
            item = parse_selection_item(raw)
        except ValueError as error:
            print(error)
            continue
        measure = measures.get(item.measure_id)
        if measure is None:
            print("Такой ID отсутствует в каталоге.")
            continue
        raw_items.append(raw)
        selected_cost = sum(
            measures[parse_selection_item(value).measure_id].cost
            for value in raw_items
        )
        print(f"Добавлено: {measure.name}. Предварительный бюджет: {selected_cost}/100.")

    result = score(selection_from_inputs(raw_items), dataset)
    print(format_result(result))
    print("\nAI-АНАЛИЗ")
    print(explain(result))


if __name__ == "__main__":
    main()
