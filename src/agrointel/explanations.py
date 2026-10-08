"""Local one-feature-at-a-time sensitivity, not SHAP or causal attribution."""

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from .config import ROOT, CFEATURES, RFEATURES


@lru_cache(maxsize=1)
def reference():
    return json.loads((ROOT / "artifacts/explanation_reference.json").read_text(encoding="utf-8"))


def crop_sensitivity(classifier, values, probabilities):
    """Batch seven median-replacement probes for all recommended classes."""
    ref = reference()["classifier_medians"]
    probes = np.tile(np.asarray(values, dtype=float), (len(CFEATURES), 1))
    for index, feature in enumerate(CFEATURES):
        probes[index, index] = ref[feature]
    probe_probabilities = classifier.predict_proba(pd.DataFrame(probes, columns=CFEATURES))
    explanations = {}
    for index in np.argsort(-probabilities)[:3]:
        impacts = [
            {
                "feature": feature,
                "input": float(values[j]),
                "reference": ref[feature],
                "probability_delta": float(probabilities[index] - probe_probabilities[j, index]),
            }
            for j, feature in enumerate(CFEATURES)
        ]
        explanations[str(classifier.classes_[index])] = {
            "method": "one_feature_median_replacement",
            "reference_source": "classifier training partition medians",
            "features": sorted(
                impacts, key=lambda item: abs(item["probability_delta"]), reverse=True
            ),
            "interpretation": "Positive delta: the supplied value supports this crop relative to replacing it with the training median. Deltas do not sum to the probability and are not causal or SHAP values.",
        }
    return explanations


def yield_sensitivity(regressor, record, predicted):
    ref = reference()["regressor_medians"]
    probes = []
    for feature in ("year", "area"):
        probe = dict(record)
        probe[feature] = ref[feature]
        probes.append(probe)
    predictions = np.maximum(0, regressor.predict(pd.DataFrame(probes, columns=RFEATURES)))
    return {
        "method": "numeric_feature_median_replacement",
        "features": [
            {
                "feature": feature,
                "input": record[feature],
                "reference": ref[feature],
                "yield_delta": float(predicted - predictions[i]),
            }
            for i, feature in enumerate(("year", "area"))
        ],
        "interpretation": "Sensitivity in tonnes/hectare, keeping crop and geography fixed. Not causal. Categorical substitutions are omitted to avoid inventing unsupported locations.",
    }
