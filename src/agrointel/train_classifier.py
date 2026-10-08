import time
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.calibration import CalibratedClassifierCV
from .config import CONFIG, CFEATURES
from .preprocessing import classification_pipeline
from .evaluation import classification_metrics


def train(frame):
    xtrain, xtest, ytrain, ytest = train_test_split(
        frame[CFEATURES],
        frame.label,
        test_size=CONFIG["classifier_test_fraction"],
        stratify=frame.label,
        random_state=CONFIG["seed"],
    )
    candidates = {
        "dummy": DummyClassifier(strategy="prior"),
        "decision_tree": DecisionTreeClassifier(max_depth=14, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=CONFIG["tree_count"],
            min_samples_leaf=1,
            n_jobs=CONFIG["workers"],
            random_state=CONFIG["seed"],
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=CONFIG["tree_count"], n_jobs=CONFIG["workers"], random_state=CONFIG["seed"]
        ),
    }
    comparisons = []
    fitted = {}
    folds = StratifiedKFold(3, shuffle=True, random_state=42)
    for name, estimator in candidates.items():
        started = time.perf_counter()
        pipe = classification_pipeline(estimator)
        scores = cross_val_score(pipe, xtrain, ytrain, cv=folds, scoring="f1_macro", n_jobs=1)
        pipe.fit(xtrain, ytrain)
        fitted[name] = pipe
        comparisons.append(
            dict(
                task="classification",
                model=name,
                validation_macro_f1=float(scores.mean()),
                seconds=time.perf_counter() - started,
            )
        )
        print(name, scores.mean(), flush=True)
    selected = max(comparisons, key=lambda r: r["validation_macro_f1"])["model"]
    # Compare calibration on an internal holdout, never the test partition.
    xa, xb, ya, yb = train_test_split(
        xtrain, ytrain, test_size=0.2, stratify=ytrain, random_state=43
    )
    raw = classification_pipeline(candidates[selected]).fit(xa, ya)
    calibrated = CalibratedClassifierCV(
        classification_pipeline(candidates[selected]), method="sigmoid", cv=3, n_jobs=1
    ).fit(xa, ya)
    raw_score = classification_metrics(raw, xb, yb)
    calibrated_score = classification_metrics(calibrated, xb, yb)
    use_calibration = (
        calibrated_score["log_loss"] < raw_score["log_loss"]
        and calibrated_score["ece"] < raw_score["ece"]
    )
    model = (
        CalibratedClassifierCV(
            classification_pipeline(candidates[selected]), method="sigmoid", cv=3, n_jobs=1
        )
        if use_calibration
        else classification_pipeline(candidates[selected])
    )
    model.fit(xtrain, ytrain)
    metrics = {
        "selected": selected,
        "test": classification_metrics(model, xtest, ytest),
        "train": classification_metrics(model, xtrain, ytrain),
        "baseline_test": classification_metrics(fitted["dummy"], xtest, ytest),
        "train_rows": len(xtrain),
        "test_rows": len(xtest),
        "calibration": {
            "used": use_calibration,
            "raw_validation": raw_score,
            "sigmoid_validation": calibrated_score,
        },
    }
    return model, metrics, comparisons, xb, yb, xtest, ytest
