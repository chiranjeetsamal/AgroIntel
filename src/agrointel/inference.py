"""Saved-artifact prediction; suitable for later MCP wrapping."""

import json
import hashlib
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from .config import ROOT, CFEATURES, RFEATURES
from .validation import validate
from .explanations import crop_sensitivity, yield_sensitivity


@lru_cache(maxsize=1)
def artifacts():
    meta = json.loads((ROOT / "artifacts/metadata.json").read_text(encoding="utf-8"))
    for name in ("crop_classifier.joblib", "yield_regressor.joblib"):
        expected = meta.get("artifact_sha256", {}).get(name)
        if (
            not expected
            or hashlib.sha256((ROOT / "artifacts" / name).read_bytes()).hexdigest() != expected
        ):
            raise RuntimeError(f"Model integrity check failed: {name}")
    return (
        joblib.load(ROOT / "artifacts/crop_classifier.joblib"),
        joblib.load(ROOT / "artifacts/yield_regressor.joblib"),
        meta,
    )


def predict_crop_and_yield(request: dict, *, explain: bool = True) -> dict:
    r = validate(request)
    classifier, regressor, meta = artifacts()
    values = [
        r[k]
        for k in [
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
        ]
    ]
    warnings = []
    for key, value in zip(CFEATURES, values):
        lo, hi = meta["classifier_ranges"][key]
        if not lo <= value <= hi:
            warnings.append(f"{key} outside training range [{lo}, {hi}]")
    if not meta["yield_years"][0] <= r["year"] <= meta["yield_years"][1]:
        warnings.append("Year outside historical training coverage; tree extrapolation is limited")
    if not meta["area_range"][0] <= r["area"] <= meta["area_range"][1]:
        warnings.append("Area outside training range")
    probabilities = classifier.predict_proba(pd.DataFrame([values], columns=CFEATURES))[0]
    explanations = crop_sensitivity(classifier, values, probabilities) if explain else {}
    recommendations = []
    coverage = set(tuple(v) for v in meta["supported_combinations"])
    for i in np.argsort(-probabilities)[:3]:
        crop = str(classifier.classes_[i])
        mapped = meta["crop_mapping"].get(crop)
        combo = (r["state"], r["district"], mapped, r["season"])
        status = (
            "supported"
            if combo in coverage
            else ("crop_unavailable" if mapped is None else "region_season_unavailable")
        )
        prediction = None
        yield_explanation = None
        if status == "supported":
            record = dict(
                state=r["state"],
                district=r["district"],
                crop=mapped,
                season=r["season"],
                year=r["year"],
                area=r["area"],
            )
            prediction = max(
                0.0, float(regressor.predict(pd.DataFrame([record], columns=RFEATURES))[0])
            )
            if explain:
                yield_explanation = yield_sensitivity(regressor, record, prediction)
        else:
            warnings.append(f"{crop}: {status}")
        recommendations.append(
            dict(
                crop=crop,
                suitability_probability=float(probabilities[i]),
                estimated_yield=prediction,
                yield_unit="tonnes/hectare",
                yield_status=status,
                explanation=explanations.get(crop, {"status": "disabled"}),
                yield_explanation=yield_explanation,
            )
        )
    return dict(
        recommendations=recommendations,
        warnings=warnings,
        classifier_version=meta["version"],
        regressor_version=meta["version"],
        training_data_coverage={
            "yield_years": meta["yield_years"],
            "crop_classes": len(classifier.classes_),
        },
        application_version="1.0.0",
        limitations=[
            "Benchmark probabilities are not probabilities of farm success.",
            "Regional yield estimates use historical 1998–2010 training data, not modern field measurements.",
            "Local sensitivity explanations are not causal effects or additive SHAP values.",
        ],
    )
