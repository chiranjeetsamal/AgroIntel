# AgroIntel 1.0 — final implementation

Verified on 8 October 2026, Python 3.12.14, Windows.

## Delivered

- Existing trained crop classifier and regional yield regressor preserved; no unnecessary retraining.
- Shared validated prediction function exposed through Python, CLI, REST and official MCP SDK stdio tools.
- Responsive browser dashboard with coverage-dependent location selectors, demo input, top-three crops, supported yield estimates, explanations, warnings and JSON/CSV export.
- Training-only median-replacement sensitivity for seven crop features and the two numeric yield features. Explicitly non-causal and not SHAP.
- Optional Open-Meteo weather context, with time/source attribution and graceful failure. Current weather never silently substitutes historical benchmark inputs.
- Model hash checks, strict request types, bounded JSON bodies, loopback defaults, same-origin/host checks and security headers.
- Offline, self-contained API explorer, reproducible dependency lock, architecture, demo/MCP documentation, Docker/Compose recipe and Windows/Linux CI configuration.
- Local Codex registration for `agrointel`, preserving unrelated settings. A client restart/new session may be required to load newly added tools.

## Evidence

- 35 automated tests passed, including actual MCP subprocess initialization, tool listing, tool calls, invalid requests, unknown geography, REST parity, local explanation arithmetic, weather success/failure and corrupt-model rejection. See test_results.xml.
- Ruff formatting/lint passed; pip reports no broken requirements.
- Browser verified historical demo prediction, explanation expansion, JSON export, clearing stale results after input changes, historical-coverage warning and mobile layout without horizontal overflow.
- Independent MCP client evidence is saved in mcp_smoke.json.
- Real Open-Meteo request succeeded for coarse public Bengaluru coordinates (12.97, 77.59). These are test coordinates, not the user's location.

## Unchanged held-out model results

Crop accuracy 99.55%, top-three accuracy 100%, macro-F1 approximately 0.99545 (440 test records). Historical yield MAE 0.626 t/ha, RMSE 2.088 t/ha, R² 0.9304 (2,275 test records from 2011–2012). These are benchmark results, not field-success guarantees.

## Honest boundaries

This is a completed local academic application, not a production farm advisory service. Public cloud hosting, authentication/TLS and present-day agronomic validation are not included or claimed. Docker is not installed on this host, so its provided recipe has not been executed. The CI workflow is configured, not claimed to have run remotely. The test environment emits a Starlette deprecation warning about its httpx test adapter; it does not affect the passing functional tests.

Student names and existing report details in the local project were preserved. Public publishing uses separate privacy-redacted text copies, leaving local identity details untouched. Raw datasets, virtual environments and Git history are excluded from delivery archives and public uploads.
