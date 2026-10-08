# Final project demonstration

1. Start the dashboard: `.venv/Scripts/python.exe -m agrointel.web`.
2. Open http://127.0.0.1:8000. Click **Load demo**, then **Find suitable crops**.
3. Explain that rice ranks first. Jute receives no yield because its production unit is incompatible with this yield model. Show the visible coverage warning.
4. Expand **What influenced this recommendation?** Explain the median-replacement method and the non-causal limitation.
5. Download JSON or CSV. Change the year to 2026, rerun and show the historical-coverage warning. Changing an input clears old results to prevent stale exports.
6. Optionally fetch weather for coordinates of your choice. The UI discloses the external request and leaves prediction inputs unchanged.
7. Show held-out metrics and source/limitations in the model section.
8. Demonstrate the same prediction with the CLI and with the registered Codex MCP server (see MCP_SETUP.md).

## What is completed

Source acquisition/audit, cleaning, feature pipelines, baseline/model comparison, efficient training, evaluation and figures, saved models, input validation, global importance, local sensitivity explanations, Python API, CLI, browser dashboard, REST API, MCP tools, optional weather context, JSON/CSV exports, automated tests, deployment recipe and documentation.

## What is not claimed

Public cloud hosting, authentication, proven real-farm accuracy, modern boundary harmonisation, a seasonal weather forecast, or causal explanations. Container recipes are provided; Docker must be installed to build them. Historical-data limitations remain even when software implementation is complete.
