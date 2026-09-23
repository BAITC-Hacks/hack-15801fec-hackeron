"""Deterministic, dependency-free Astana Quality of Life Score calculation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.validator import Selection, ValidationResult, validate

if TYPE_CHECKING:
    from src.data import Dataset


@dataclass(frozen=True)
class IndicatorDelta:
    """The net change of one indicator in one district."""

    district_id: str
    indicator: str
    before: float
    after: float
    delta: float


@dataclass(frozen=True)
class DistrictResult:
    """Scores and indicator changes for one district."""

    district_id: str
    district_name: str
    before: float
    after: float
    deltas: tuple[IndicatorDelta, ...]


@dataclass(frozen=True)
class MeasureContribution:
    """One lag-scaled measure or synergy effect applied to a district."""

    measure_id: str
    district_id: str
    indicator: str
    delta: float


@dataclass(frozen=True)
class ScoreResult:
    """A complete audit trail for a valid selection, or validation failure."""

    valid: bool
    validation: ValidationResult
    budget_used: int
    cost_total: int
    districts: tuple[DistrictResult, ...]
    d_avg: float | None
    min_district: float | None
    n_crit: int | None
    score: float | None
    score_delta: float | None
    contributions: tuple[MeasureContribution, ...]


def score(selection: Selection, dataset: "Dataset") -> ScoreResult:
    """Validate and score a decision set; invalid selections receive no score."""
    validation = validate(selection, dataset)
    measures = {measure.id: measure for measure in dataset.measures}
    cost_total = sum(
        measures[item.measure_id].cost
        for item in selection.items
        if item.measure_id in measures
    )
    if not validation.valid:
        return ScoreResult(
            valid=False,
            validation=validation,
            budget_used=cost_total,
            cost_total=cost_total,
            districts=(),
            d_avg=None,
            min_district=None,
            n_crit=None,
            score=None,
            score_delta=None,
            contributions=(),
        )
    result = _calculate(selection, dataset)
    baseline = _calculate(Selection(()), dataset)
    return ScoreResult(
        valid=True,
        validation=validation,
        budget_used=cost_total,
        cost_total=cost_total,
        districts=result.districts,
        d_avg=result.d_avg,
        min_district=result.min_district,
        n_crit=result.n_crit,
        score=result.score,
        score_delta=result.score - baseline.score,
        contributions=result.contributions,
    )


def score_baseline(dataset: "Dataset") -> ScoreResult:
    """Return the no-action baseline without applying the five-decision rule."""
    result = _calculate(Selection(()), dataset)
    return ScoreResult(
        valid=True,
        validation=ValidationResult(True, ()),
        budget_used=0,
        cost_total=0,
        districts=result.districts,
        d_avg=result.d_avg,
        min_district=result.min_district,
        n_crit=result.n_crit,
        score=result.score,
        score_delta=0.0,
        contributions=(),
    )


def _calculate(selection: Selection, dataset: "Dataset") -> ScoreResult:
    """Apply effects and calculate scores; callers handle selection validity."""
    measures = {measure.id: measure for measure in dataset.measures}
    districts = {district.id: district for district in dataset.districts}
    horizon = float(dataset.rules["horizon_quarters"])
    changes = {
        district.id: {indicator: 0.0 for indicator in dataset.indicators}
        for district in dataset.districts
    }
    contributions: list[MeasureContribution] = []

    for item in selection.items:
        measure = measures[item.measure_id]
        target_ids = tuple(districts) if measure.type == "city" else (item.district,)
        scale = (horizon - measure.lag) / horizon
        for district_id in target_ids:
            for indicator, effect in measure.effects.items():
                delta = effect * scale
                changes[district_id][indicator] += delta
                contributions.append(
                    MeasureContribution(measure.id, district_id, indicator, delta)
                )

    selected = {item.measure_id: item for item in selection.items}
    for synergy in dataset.rules["synergies"]:
        first, second = synergy["measures"]
        if first not in selected or second not in selected:
            continue
        district_id = selected[synergy["district_from"]].district
        delta = float(synergy["delta"])
        indicator = synergy["indicator"]
        changes[district_id][indicator] += delta
        contributions.append(
            MeasureContribution(f"{first}+{second}", district_id, indicator, delta)
        )

    weights = dataset.rules["weights"]
    district_results: list[DistrictResult] = []
    after_scores: list[float] = []
    n_crit = 0
    threshold = float(dataset.rules["critical_threshold"])
    for district in dataset.districts:
        deltas: list[IndicatorDelta] = []
        after_indicators: dict[str, float] = {}
        for indicator in dataset.indicators:
            before = float(district.indicators[indicator])
            after = min(100.0, max(0.0, before + changes[district.id][indicator]))
            after_indicators[indicator] = after
            deltas.append(IndicatorDelta(district.id, indicator, before, after, after - before))
            n_crit += after < threshold
        before_score = _district_score(district.indicators, weights)
        after_score = _district_score(after_indicators, weights)
        after_scores.append(after_score)
        district_results.append(
            DistrictResult(district.id, district.name, before_score, after_score, tuple(deltas))
        )

    d_avg = sum(
        district.population_share * district_result.after
        for district, district_result in zip(dataset.districts, district_results)
    )
    min_district = min(after_scores)
    final_score = 0.7 * d_avg + 0.3 * min_district - n_crit
    return ScoreResult(
        valid=True,
        validation=ValidationResult(True, ()),
        budget_used=0,
        cost_total=0,
        districts=tuple(district_results),
        d_avg=d_avg,
        min_district=min_district,
        n_crit=n_crit,
        score=final_score,
        score_delta=0.0,
        contributions=tuple(contributions),
    )


def _district_score(indicators: object, weights: object) -> float:
    return sum(float(weights[indicator]) * float(indicators[indicator]) for indicator in weights)
