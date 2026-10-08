"""Read-only model and coverage information, without personal project details."""

import json
from functools import lru_cache

from .config import ROOT
from .data import normalise
from .inference import artifacts


@lru_cache(maxsize=1)
def combinations():
    return tuple(tuple(row) for row in artifacts()[2]["supported_combinations"])


def list_supported_locations(state: str = "", district: str = "", season: str = "") -> dict:
    state, district, season = map(normalise, (state, district, season))
    rows = [
        row
        for row in combinations()
        if (not state or row[0] == state)
        and (not district or row[1] == district)
        and (not season or row[3] == season)
    ]
    return {
        "states": sorted({row[0] for row in combinations()}),
        "districts": sorted({row[1] for row in rows}),
        "seasons": sorted({row[3] for row in rows}),
        "crops": sorted({row[2] for row in rows}),
        "matching_combinations": len(rows),
        "note": "Historical source labels; contemporary administrative boundaries may differ.",
    }


def get_model_info() -> dict:
    classifier, _, meta = artifacts()
    metrics = json.loads((ROOT / "reports/metrics.json").read_text(encoding="utf-8"))
    return {
        "application_version": "1.0.0",
        "model_version": meta["version"],
        "crop_classes": [str(crop) for crop in classifier.classes_],
        "yield_supported_crops": sorted(meta["crop_mapping"]),
        "training_years": meta["yield_years"],
        "input_ranges": meta["classifier_ranges"],
        "units": meta["units"],
        "metrics": metrics,
        "source_links": [source["url"] for source in meta["sources"]],
        "limitations": [
            "Academic prototype, not agronomic advice.",
            "Nutrient units and rainfall aggregation period in the benchmark are unverified.",
            "Yield data are a community snapshot attributed to government records.",
            "Historical regional boundaries are not harmonised.",
            "No guarantee of performance on present-day farms.",
        ],
    }
