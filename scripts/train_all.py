"""End-to-end audited training with a single untouched final test per task."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
from pathlib import Path
import sys
import json
import time
import platform
import importlib.metadata
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
from agrointel.config import ROOT, CONFIG, CFEATURES, RFEATURES, CROP_MAP
from agrointel.data import load_clean
from agrointel.train_classifier import train as train_classifier
from agrointel.train_regressor import train as train_regressor


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def main():
    started = time.perf_counter()
    for directory in ["artifacts", "reports/figures", "examples"]:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)
    a, b, audit = load_clean()
    print("CLEAN DATA", len(a), len(b), audit["years"], flush=True)
    write_json(ROOT / "reports/data_audit.json", audit)
    classifier, cm, cc, xv, yv, xt, yt = train_classifier(a)
    joblib.dump(classifier, ROOT / "artifacts/crop_classifier.joblib", compress=3)
    regressor, rm, rc, fit, val, test, pred = train_regressor(b)
    joblib.dump(regressor, ROOT / "artifacts/yield_regressor.joblib", compress=3)
    ranges = {c: [float(a[c].min()), float(a[c].max())] for c in CFEATURES}
    meta = {
        "version": "0.1.0",
        "seed": 42,
        "classifier_features": CFEATURES,
        "regressor_features": RFEATURES,
        "classifier_ranges": ranges,
        "yield_years": rm["fit_years"],
        "area_range": [float(fit.area.min()), float(fit.area.max())],
        "crop_mapping": {k: v for k, v in CROP_MAP.items() if v in set(fit.crop)},
        "supported_combinations": fit[["state", "district", "crop", "season"]]
        .drop_duplicates()
        .values.tolist(),
        "config": CONFIG,
        "sources": json.loads((ROOT / "data/provenance/sources.json").read_text()),
        "packages": {
            p: importlib.metadata.version(p)
            for p in ["scikit-learn", "pandas", "numpy", "joblib", "matplotlib"]
        },
        "units": {
            "N/P/K": "source benchmark scale; physical units unverified",
            "temperature": "Celsius",
            "humidity": "percent",
            "ph": "pH",
            "rainfall": "mm",
            "area": "hectares",
            "production": "tonnes for retained crops",
            "yield": "tonnes/hectare",
        },
        "runtime": {"python": platform.python_version(), "cpu_count": os.cpu_count()},
    }
    write_json(ROOT / "artifacts/metadata.json", meta)
    meta["artifact_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "artifacts").glob("*.joblib")
    }
    write_json(ROOT / "artifacts/metadata.json", meta)
    from build_explanation_reference import main as build_reference

    build_reference()
    write_json(ROOT / "reports/metrics.json", {"classification": cm, "regression": rm})
    pd.DataFrame(cc + rc).to_csv(ROOT / "reports/model_comparison.csv", index=False)
    pd.DataFrame(
        classification_report(yt, classifier.predict(xt), output_dict=True)
    ).transpose().to_csv(ROOT / "reports/classification_by_crop.csv")
    breakdown = test[["crop", "district", "year", "yield"]].copy()
    breakdown["prediction"] = pred
    breakdown["absolute_error"] = abs(breakdown["yield"] - pred)
    breakdown.to_csv(ROOT / "reports/regression_test_predictions.csv", index=False)
    for group in ["crop", "district"]:
        breakdown.groupby(group).absolute_error.agg(["count", "mean", "median"]).to_csv(
            ROOT / f"reports/error_by_{group}.csv"
        )
    from sklearn.base import clone

    pre_class = a.drop(index=xv.index.union(xt.index))
    explanation_classifier = clone(classifier).fit(pre_class[CFEATURES], pre_class.label)
    importance = permutation_importance(
        explanation_classifier, xv, yv, n_repeats=3, random_state=42, scoring="f1_macro", n_jobs=1
    )
    pd.DataFrame({"feature": CFEATURES, "importance": importance.importances_mean}).to_csv(
        ROOT / "reports/classifier_importance.csv", index=False
    )
    # Fit temporary model only on pre-validation years for uncontaminated importance.
    from sklearn.base import clone

    pre = fit[fit.year < min(rm["validation_years"])]
    development = clone(regressor).fit(pre[RFEATURES], pre["yield"])
    sample = val.sample(min(1000, len(val)), random_state=42)
    ri = permutation_importance(
        development,
        sample[RFEATURES],
        sample["yield"],
        n_repeats=2,
        random_state=42,
        scoring="neg_mean_absolute_error",
        n_jobs=1,
    )
    pd.DataFrame({"feature": RFEATURES, "importance": ri.importances_mean}).to_csv(
        ROOT / "reports/regressor_importance.csv", index=False
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    a.label.value_counts().plot.bar(ax=ax)
    ax.set_title("Crop benchmark class distribution")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/class_balance.png")
    plt.close(fig)
    fig, axes = plt.subplots(2, 4, figsize=(12, 6))
    a[CFEATURES].hist(ax=axes.ravel()[:7], bins=25)
    axes.ravel()[-1].axis("off")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/feature_distributions.png")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 9))
    ConfusionMatrixDisplay.from_estimator(
        classifier, xt, yt, ax=ax, xticks_rotation=90, colorbar=False
    )
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/confusion_matrix.png")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(CFEATURES, importance.importances_mean)
    ax.set_xlabel("Validation macro-F1 decrease")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/classifier_importance.png")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(test["yield"], pred, s=4, alpha=0.2)
    ax.set_xlabel("Actual tonnes/hectare")
    ax.set_ylabel("Predicted tonnes/hectare")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/figures/yield_predictions.png")
    plt.close(fig)
    supported = fit[fit.crop == "rice"].iloc[0]
    soil = a[a.label == "rice"].iloc[0]
    request = dict(
        zip(
            ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"],
            [float(soil[c]) for c in CFEATURES],
        )
    )
    request.update(
        state=str(supported.state),
        district=str(supported.district),
        season=str(supported.season),
        year=int(fit.year.max()),
        area=float(supported.area),
    )
    write_json(ROOT / "examples/request.json", request)
    audit_text = (
        "# Data audit\n\n"
        + json.dumps(audit, indent=2)
        + "\n\nRegional source is a pre-cleaned community copy attributed to the Government of India. Raw means unchanged downloaded snapshot, not original government records. Units for retained crops follow publisher documentation. Historical boundaries are not harmonised. Existing source yield was ignored and recomputed. No statistical clipping or synthetic rows.\n"
    )
    (ROOT / "reports/data_audit.md").write_text(audit_text, encoding="utf-8")
    summary = f"# Review summary\n\nStudents: Student A ([registration omitted]), Student B ([registration omitted]). BCSE206L, SCOPE & SENSE.\n\nCompleted: acquisition, audit, preprocessing, model comparison, trained artifacts, held-out evaluation, global validation importance, local CLI, MCP stdio tools, REST dashboard, local median-replacement sensitivity, optional weather context, export, tests and deployment recipe.\n\nDeployment boundary: local academic prototype. Public hosting and production security are not claimed.\n\nClassification: {json.dumps(cm)}\n\nRegression: {json.dumps(rm)}\n\nYield overlap: {json.dumps(meta['crop_mapping'])}\n\nHistorical data is old; later years require extrapolation warnings. Suitability probabilities describe benchmark classification, not farm success. Yield extremes remain and can increase RMSE. Source chain and nutrient units remain limited.\n\nElapsed seconds: {time.perf_counter() - started:.1f}\n"
    (ROOT / "reports/review_summary.md").write_text(summary, encoding="utf-8")
    print(json.dumps({"classification": cm, "regression": rm}, indent=2), flush=True)


if __name__ == "__main__":
    main()
