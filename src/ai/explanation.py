"""Fact-grounded Russian explanation of a precomputed simulator result.

This module deliberately never imports scoring internals or recalculates a score.
An optional LLM receives a prompt containing only the already-computed audit trail.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from src.engine import ScoreResult


class NarrativeModel(Protocol):
    """Minimal adapter for any chat model provider."""

    def complete(self, prompt: str) -> str:
        """Return a Russian narrative for the supplied fact-only prompt."""


def build_prompt(result: ScoreResult, question: str | None = None) -> str:
    """Build an LLM-ready prompt using only values already present in ``result``."""
    rules = [
        "Ты объясняешь результат симулятора городских решений на русском языке.",
        "Используй только факты ниже. Не считай, не пересчитывай, не округляй по-своему "
        "и не придумывай чисел, причин или эффектов.",
        "Опиши сильные стороны, риски и компромиссы кратко и понятно.",
    ]
    if not result.valid:
        reasons = "\n".join(f"- {reason}" for reason in result.validation.reasons)
        return "\n".join(rules + ["Набор недействителен; Score не рассчитан.", reasons])

    districts = "\n".join(
        "- {name}: {before:.2f} → {after:.2f}; изменения: {changes}".format(
            name=district.district_name,
            before=district.before,
            after=district.after,
            changes=", ".join(
                f"{delta.indicator} {delta.delta:+.2f}"
                for delta in district.deltas
                if delta.delta
            ) or "нет",
        )
        for district in result.districts
    )
    contributions = "\n".join(
        f"- {item.measure_id}, {item.district_id}: {item.indicator} {item.delta:+.2f}"
        for item in result.contributions
    ) or "- нет"
    facts = [
        "ФАКТЫ ИЗ ДЕТЕРМИНИРОВАННОГО РАСЧЁТА:",
        f"Бюджет: {result.budget_used}.",
        f"Score: {result.score:.2f}; изменение к базе: {result.score_delta:+.2f}.",
        f"Среднее по городу: {result.d_avg:.2f}; минимум среди районов: {result.min_district:.2f}; "
        f"критических значений: {result.n_crit}.",
        "Районы:\n" + districts,
        "Вклады мер и синергий:\n" + contributions,
    ]
    if question:
        facts.append(f"Вопрос пользователя: {question}")
    return "\n".join(rules + facts)


def explain(
    result: ScoreResult,
    question: str | None = None,
    model: NarrativeModel | Callable[[str], str] | None = None,
) -> str:
    """Explain a result with an injected model, or use the safe local fallback.

    Provider integration remains an adapter concern: pass an object implementing
    ``complete(prompt)`` or a callable. No API key, network access, or arithmetic is
    hidden inside this module.
    """
    prompt = build_prompt(result, question)
    if model is None:
        return _local_explanation(result, question)
    if callable(model):
        return model(prompt)
    return model.complete(prompt)


def _local_explanation(result: ScoreResult, question: str | None) -> str:
    """Give an offline narrative by quoting, rather than deriving, engine facts."""
    if not result.valid:
        return "Сценарий не принят: " + "; ".join(result.validation.reasons)

    lines = [
        "Итог сценария",
        f"Score: {result.score:.2f} ({result.score_delta:+.2f} к базовому сценарию).",
        f"Использовано {result.budget_used} из 100 единиц бюджета.",
        f"Среднее по городу — {result.d_avg:.2f}, минимум среди районов — "
        f"{result.min_district:.2f}; критических значений — {result.n_crit}.",
        "Наблюдаемые изменения:",
    ]
    for district in result.districts:
        changed = [f"{delta.indicator} {delta.delta:+.2f}" for delta in district.deltas if delta.delta]
        if changed:
            lines.append(f"• {district.district_name}: " + ", ".join(changed) + ".")
    if result.n_crit:
        lines.append("Риск: после сценария остаются критические показатели; им нужен приоритет.")
    else:
        lines.append("Критических показателей ниже порога после сценария не осталось.")
    if question:
        lines.append(f"Учтён вопрос пользователя: {question}")
    return "\n".join(lines)
