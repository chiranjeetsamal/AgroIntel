# Connect AgroIntel to Codex

Install the project dependencies first. The server uses the official Python MCP SDK and stdio transport; it does not need an OpenAI API key. Codex chooses the tool and displays its output; the Python models produce every prediction.

From PowerShell, register this project's absolute launcher:

```powershell
codex mcp add agrointel -- E:/codex/FDS/agrointel/.venv/Scripts/python.exe E:/codex/FDS/agrointel/scripts/run_mcp.py
codex mcp get agrointel
```

If you move the checkout, replace both paths. Alternatively, merge deploy/codex-config.example.toml into your Codex configuration. Never overwrite existing unrelated MCP entries. Restart/reopen the client if the tools do not appear in the current session.

Official configuration reference: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
Official SDK: https://github.com/modelcontextprotocol/python-sdk

## Tools

- `get_model_info`: scope, units, evaluation results and limitations.
- `list_supported_locations`: historical location, season and crop coverage.
- `predict_crop_and_yield`: strict `request` object with all twelve required fields, plus optional `explain` boolean.
- `get_live_weather`: optional latitude/longitude request; sends coordinates to Open-Meteo. Not a replacement for the model's benchmark climate values.

Example Codex prompt:

> Use AgroIntel to predict crops for nitrogen 90, phosphorus 42, potassium 43, temperature 20.87974371 Celsius, humidity 82.00274423 percent, pH 6.502985292, benchmark rainfall 202.9355362 mm, state andhra pradesh, district adilabad, season kharif, year 2010, and area 66400 hectares. Show the three recommendations, supported yield estimates, sensitivity explanations and all warnings. Do not fetch live weather.

Use historical source labels for this demo. Missing soil inputs must be requested from the user, not inferred from geography or invented. New-year predictions carry extrapolation warnings. Probabilities are benchmark suitability, not chances of agricultural success.

## Independent protocol verification

```powershell
.venv/Scripts/python.exe scripts/mcp_smoke.py
```

This launches a real subprocess, initializes an MCP client, lists tools and calls prediction over stdio. Evidence is saved to reports/mcp_smoke.json. The server keeps stdout reserved for JSON-RPC; logging goes to stderr. This proves protocol operation independently of a Codex UI session.
