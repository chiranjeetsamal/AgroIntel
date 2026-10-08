"""Persist training-only median probes without refitting or altering saved models."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from sklearn.model_selection import train_test_split
from agrointel.config import ROOT, CONFIG, CFEATURES


def main():
    crop = pd.read_csv(ROOT / "data/processed/crop.csv")
    regional = pd.read_csv(ROOT / "data/processed/yield.csv")
    train, _ = train_test_split(
        crop,
        test_size=CONFIG["classifier_test_fraction"],
        stratify=crop.label,
        random_state=CONFIG["seed"],
    )
    meta = json.loads((ROOT / "artifacts/metadata.json").read_text())
    fit = regional[regional.year.between(*meta["yield_years"])]
    reference = {
        "method": "one_feature_median_replacement",
        "classifier_medians": {key: float(train[key].median()) for key in CFEATURES},
        "regressor_medians": {key: float(fit[key].median()) for key in ("year", "area")},
        "classifier_rows": len(train),
        "regressor_rows": len(fit),
        "note": "Training-only reference values; no test records used. Non-causal sensitivity, not SHAP.",
    }
    (ROOT / "artifacts/explanation_reference.json").write_text(
        json.dumps(reference, indent=2), encoding="utf-8"
    )
    print(json.dumps(reference, indent=2))


if __name__ == "__main__":
    main()
