"""Loading and validating the source-traceable simulator dataset."""
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

class DatasetError(ValueError):
    """Raised when a bundled data file does not meet the pinned contract."""

@dataclass(frozen=True)
class District:
    id: str
    name: str
    population_share: float
    indicators: Mapping[str, float]

@dataclass(frozen=True)
class Measure:
    id: str
    direction: str
    name: str
    type: str
    cost: int
    lag: int
    effects: Mapping[str, float]

@dataclass(frozen=True)
class Dataset:
    indicators: tuple[str, ...]
    districts: tuple[District, ...]
    measures: tuple[Measure, ...]
    rules: Mapping[str, Any]

def load_dataset(data_dir: Path | str | None = None) -> Dataset:
    root = Path(data_dir) if data_dir else Path(__file__).resolve().parents[2] / "data"
    districts_doc = _read(root / "districts.json")
    measures_doc = _read(root / "measures.json")
    rules = _read(root / "rules.json")
    indicators = tuple(districts_doc.get("indicators", ()))
    if len(indicators) != 10 or len(set(indicators)) != len(indicators):
        raise DatasetError("districts.json must define 10 unique indicators")
    districts = tuple(District(**item) for item in districts_doc.get("districts", ()))
    measures = tuple(Measure(**item) for item in measures_doc.get("measures", ()))
    if len(districts) != 5 or sum(d.population_share for d in districts) != 1.0:
        raise DatasetError("districts must contain five entries whose population shares total 1")
    if len(measures) != 14 or len({m.id for m in measures}) != 14:
        raise DatasetError("measures.json must contain 14 uniquely identified measures")
    if any(set(d.indicators) != set(indicators) for d in districts):
        raise DatasetError("every district must define every indicator")
    if any(set(m.effects) - set(indicators) for m in measures):
        raise DatasetError("measure effects may only use declared indicators")
    return Dataset(indicators, districts, measures, rules)

def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetError(f"cannot load {path}: {exc}") from exc
