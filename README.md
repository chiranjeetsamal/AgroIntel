# AgroIntel

Explainable crop recommendation and regional yield forecasting. Foundations of Data Science, BCSE206L. Student A — [registration omitted]; Student B — [registration omitted]; SCOPE & SENSE.

## Setup (Python 3.11 or newer)

Run from this project directory on Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe -m agrointel.cli examples/request.json --output examples/response.json
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m agrointel.web
```

The distributed model files support immediate prediction without downloading training data. Install the exact versions in `requirements-lock.txt` to reproduce the saved model environment. Scikit-learn joblib files must come from a trusted source and are not portable across arbitrary library versions.

Open **http://127.0.0.1:8000**. Load the historical demo, generate predictions, inspect local sensitivity, and download JSON/CSV. The interface works without external fonts, scripts or a frontend build step. Optional weather needs internet; predictions do not. The saved model environment was verified on Python 3.12; use that version for reproducibility. The API explorer at `/docs` is self-contained and does not load CDN assets.

## Codex MCP integration

```powershell
codex mcp add agrointel -- E:/codex/FDS/agrointel/.venv/Scripts/python.exe E:/codex/FDS/agrointel/scripts/run_mcp.py
.venv\Scripts\python.exe scripts/mcp_smoke.py
```

Replace both paths if the checkout moves. Four tools expose predictions, model information, supported locations, and optional live weather. No OpenAI API key is required by this local server. See [MCP setup](docs/MCP_SETUP.md) for a ready-to-use Codex prompt and official references. A client restart/new session may be needed to load a newly registered server.

## REST API and deployment

`GET /api/health`, `/api/model-info`, `/api/coverage`, `/api/example`, `/api/weather`; `POST /api/predict` accepts the same JSON as the CLI. Interactive API documentation: http://127.0.0.1:8000/docs. Predictions include seven-feature local crop sensitivity and numeric yield sensitivity, with explicit non-causal limitations. Extra/invalid fields are rejected.

With Docker installed: `docker compose up --build`. The provided configuration is local-only and uses a non-root container with read-only storage. Docker has not been run on the development host; see [architecture and security boundaries](docs/ARCHITECTURE.md). Public hosting requires authentication, TLS, resource limits and a deployment destination. No cloud deployment is claimed. Wheel installs must set `AGROINTEL_ROOT` to the checkout containing artifacts/configs; editable installs resolve the checkout automatically.

## Retrain from source (optional)

```powershell
.venv\Scripts\python.exe scripts/download_data.py
.venv\Scripts\python.exe scripts/train_all.py
.venv\Scripts\python.exe scripts/finalize.py
.venv\Scripts\python.exe -m agrointel.cli examples/request.json --output examples/response.json
```

Retraining recreates model hashes and training-only explanation references. Restart running web/MCP servers to clear loaded-model caches. Keep the downloaded source hashes for reproduction. Retraining is not needed for the bundled demo.

## Models and split design

The classifier uses seven benchmark features, a stratified 80:20 held-out test, three-fold model selection and a separate internal calibration comparison. The selected estimator is fitted on the training partition only. Random seed is 42.

The yield regressor uses state, district, crop, season, year and area, encoded with a sparse one-hot preprocessing pipeline. It compares median baseline, Extra Trees and robust Gradient Boosting on two chronological validation years, then refits the selected model on all pre-test years. The final two years remain untouched during selection. See `reports/metrics.json` for actual scores, sample counts and selected models; `reports/model_comparison.csv` records configurations' runtimes and validation results.

Configuration is in `configs/default.yaml`. The bounded model candidates are specified in the two training modules. No synthetic records or target leakage are used. Source production is removed after computing yield. Exact duplicate rows are removed; conflicting regional keys are excluded rather than summed. Statistical extremes remain.

## Data and units

Crop dataset: https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset

Regional snapshot: https://github.com/k0rn/India_Agri_Data — community cleaned copy attributed to Government of India, with CC0 declaration. It is not an independently verified original government export. Publisher documents area in hectares and production in tonnes, but crop-specific exceptions require caution. Cotton/jute (bales) and coconut (nuts) are excluded. Only explicitly mapped individual crop categories are retained. Existing yield is ignored and recomputed as production/area.

Raw source records and processed CSVs are excluded from the project ZIP. Use the acquisition script to download them. `data/provenance/sources.json` records URLs, timestamps, source dimensions and SHA256 hashes. Remote sources may change; compare their hashes when reproducing a run.

Input dictionary:

| Field | Unit / meaning |
|---|---|
| nitrogen, phosphorus, potassium | Dataset benchmark scale; physical units unverified |
| temperature | degrees Celsius |
| humidity | percent, 0–100 |
| ph | pH, 0–14 |
| rainfall | millimetres |
| state, district, season | Source labels; whitespace/case normalised |
| year | Starting calendar year of agricultural year |
| area | hectares, strictly positive |
| estimated_yield | tonnes/hectare for supported crops |

Crop mapping and geographic support are stored in `artifacts/metadata.json`. A crop without a verified mapping or a supported state/district/season receives null yield and a reason. A valid request for a year outside training coverage receives a warning. Tree models cannot infer modern agricultural changes beyond historical training years. Geographic boundary changes are not reconstructed.

## Prediction API

```python
from agrointel import predict_crop_and_yield
result = predict_crop_and_yield(request)
```

The API returns three crops ranked by benchmark classification probability, yield estimates where supported, statuses, warnings and artifact versions. Probabilities are not estimates of real farm success. Yield does not override suitability ordering. Local explanations replace one input at a time with its training median; these are sensitivity probes, not causal or additive SHAP values. Global permutation importance is computed on validation observations and saved in reports. `examples/response.json` is generated by the saved artifacts in a separate process. Use `explain=False` with the Python API to omit sensitivity probes.

## Current scope

Completed: public acquisition, source audit, EDA figures, preprocessing, baselines, model comparison, efficient training, held-out evaluation, persisted pipelines, integrity checks, Python API, CLI, MCP stdio tools, REST API, responsive dashboard, local sensitivity, JSON/CSV exports, optional live weather, automated tests, CI configuration and deployment packaging.

Remaining boundaries: public cloud hosting is not configured; Docker needs separate host verification. Agronomic field validation and modern datasets are outside this academic prototype. Current weather is contextual only and never silently substitutes model inputs. See [demo guide](docs/DEMO_GUIDE.md).

## Reports

- `data_audit.json` and `data_audit.md`: shapes, missingness, duplicates, exclusions and quality limitations.
- `metrics.json`: real final test results and calibration comparison.
- `model_comparison.csv`: validation scores and runtime.
- `classification_by_crop.csv`, `error_by_crop.csv`, `error_by_district.csv`: subgroup results.
- `figures/`: class balance, distributions, confusion matrix, validation importance and yield predictions.
- `review_summary.md`: concise review material.

Model artifacts contain no preprocessing code external to standard installed libraries. Metadata includes feature order, crop mapping, coverage, package versions and source hashes. Application version is 1.0.0; the unchanged trained models retain their own 0.1.0 version. Run `scripts/package_project.py` to create `AgroIntel_Complete_Project.zip`, excluding raw data, environments and Git history.
