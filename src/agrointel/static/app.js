"use strict";
const $ = (id) => document.getElementById(id);
const form = $("prediction-form");
let lastPrediction = null;
let coverageSequence = 0;
async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail
          .map((item) => `${item.loc.join(".")}: ${item.msg}`)
          .join("; ")
      : data.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data;
}
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function options(select, values, placeholder, chosen = "") {
  select.replaceChildren(new Option(placeholder, ""));
  for (const value of values) select.add(new Option(value, value));
  select.disabled = values.length === 0;
  select.value = chosen;
}
async function updateCoverage(level, chosen = {}) {
  const sequence = ++coverageSequence;
  const state = $("state").value;
  if (level === "state") {
    options($("district"), [], "Choose district");
    options($("season"), [], "Choose season");
  } else options($("season"), [], "Choose season");
  if (!state) return;
  const params = new URLSearchParams({ state });
  if (level === "district") params.set("district", $("district").value);
  const data = await api(`/api/coverage?${params}`);
  if (sequence !== coverageSequence) return;
  if (level === "state")
    options($("district"), data.districts, "Choose district", chosen.district);
  options($("season"), data.seasons, "Choose season", chosen.season);
}
function status(message, error = false) {
  $("form-status").textContent = message;
  $("form-status").classList.toggle("error", error);
}
function clearResults() {
  lastPrediction = null;
  $("results").hidden = true;
  $("empty-state").hidden = false;
}
async function loadExample() {
  $("load-example").disabled = true;
  try {
    const sample = await api("/api/example");
    for (const [key, value] of Object.entries(sample)) {
      if (!["district", "season"].includes(key))
        form.elements.namedItem(key).value = value;
    }
    await updateCoverage("state", sample);
    await updateCoverage("district", sample);
    status(
      "Historical demo loaded. These are sample values, not readings from your farm.",
    );
    clearResults();
  } catch (error) {
    status(error.message, true);
  } finally {
    $("load-example").disabled = false;
  }
}
function render(result) {
  $("recommendations").replaceChildren();
  result.recommendations.forEach((crop, index) => {
    const card = node("article", undefined, "crop-card");
    card.append(node("div", `RANK 0${index + 1}`, "rank"));
    const header = node("div", undefined, "crop-header");
    header.append(
      node("h3", crop.crop, "crop-name"),
      node(
        "span",
        `${(crop.suitability_probability * 100).toFixed(2)}%`,
        "probability",
      ),
    );
    card.append(
      header,
      node("div", "Benchmark suitability probability", "prob-label"),
    );
    const bar = node("progress");
    bar.max = 1;
    bar.value = crop.suitability_probability;
    bar.setAttribute("aria-label", `${crop.crop} suitability`);
    card.append(bar);
    if (crop.estimated_yield !== null) {
      const yieldText = node("p", "Historical estimated yield: ", "yield");
      yieldText.append(
        node("strong", crop.estimated_yield.toFixed(2)),
        document.createTextNode(" t/ha"),
      );
      card.append(yieldText);
    } else
      card.append(
        node(
          "p",
          crop.yield_status === "crop_unavailable"
            ? "No comparable yield data for this crop."
            : "Yield unavailable for this region and season.",
          "no-yield",
        ),
      );
    const details = node("details");
    details.append(node("summary", "What influenced this recommendation?"));
    (crop.explanation.features || []).forEach((feature) => {
      const row = node("div", undefined, "explanation-row");
      row.append(
        node(
          "span",
          `${feature.feature} · input ${feature.input.toFixed(2)} / median ${feature.reference.toFixed(2)}`,
        ),
        node(
          "span",
          `${feature.probability_delta >= 0 ? "+" : ""}${(feature.probability_delta * 100).toFixed(2)} pp`,
          `impact ${feature.probability_delta >= 0 ? "positive" : "negative"}`,
        ),
      );
      details.append(row);
    });
    details.append(
      node(
        "p",
        "One input is replaced with its training median. Positive deltas support this crop relative to that replacement; negative deltas reduce its probability. These effects do not add up and are not causal.",
        "fine",
      ),
    );
    if (crop.yield_explanation) {
      details.append(node("h4", "Yield sensitivity"));
      crop.yield_explanation.features.forEach((feature) =>
        details.append(
          node(
            "p",
            `${feature.feature}: ${feature.yield_delta >= 0 ? "+" : ""}${feature.yield_delta.toFixed(3)} t/ha relative to its training median.`,
            "fine",
          ),
        ),
      );
    }
    card.append(details);
    $("recommendations").append(card);
  });
  $("warnings").replaceChildren(
    ...result.warnings.map((warning) => node("li", warning)),
  );
  $("warning-box").hidden = result.warnings.length === 0;
  $("empty-state").hidden = true;
  $("results").hidden = false;
}
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form));
  for (const key of [
    "nitrogen",
    "phosphorus",
    "potassium",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "year",
    "area",
  ])
    payload[key] = Number(payload[key]);
  $("predict-button").disabled = true;
  $("load-example").disabled = true;
  clearResults();
  status("Comparing crops and checking regional coverage…");
  const signature = JSON.stringify(Object.fromEntries(new FormData(form)));
  try {
    const result = await api("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (signature !== JSON.stringify(Object.fromEntries(new FormData(form)))) {
      status(
        "Inputs changed while predicting. Submit the new values to refresh results.",
      );
      return;
    }
    lastPrediction = { inputs: payload, ...result };
    render(result);
    status("Prediction ready. Review the explanations and coverage warnings.");
  } catch (error) {
    clearResults();
    status(error.message, true);
  } finally {
    $("predict-button").disabled = false;
    $("load-example").disabled = false;
  }
});
form.addEventListener("input", () => {
  if (lastPrediction) {
    clearResults();
    status("Inputs changed. Generate a new prediction before exporting.");
  }
});
$("state").addEventListener("change", () =>
  updateCoverage("state").catch((error) => status(error.message, true)),
);
$("district").addEventListener("change", () =>
  updateCoverage("district").catch((error) => status(error.message, true)),
);
$("load-example").addEventListener("click", loadExample);
function download(content, type, name) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = node("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("export-json").addEventListener("click", () => {
  if (lastPrediction)
    download(
      JSON.stringify(lastPrediction, null, 2),
      "application/json",
      "agrointel-prediction.json",
    );
});
$("export-csv").addEventListener("click", () => {
  if (!lastPrediction) return;
  const rows = [
    [
      "rank",
      "crop",
      "suitability_probability",
      "estimated_yield_tonnes_per_hectare",
      "yield_status",
    ],
    ...lastPrediction.recommendations.map((crop, index) => [
      index + 1,
      crop.crop,
      crop.suitability_probability,
      crop.estimated_yield ?? "",
      crop.yield_status,
    ]),
  ];
  download(
    rows
      .map((row) =>
        row
          .map((value) => `"${String(value).replaceAll('"', '""')}"`)
          .join(","),
      )
      .join("\r\n"),
    "text/csv",
    "agrointel-prediction.csv",
  );
});
$("weather-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("weather-button").disabled = true;
  $("weather-output").textContent = "Checking Open-Meteo…";
  $("weather-output").classList.remove("error");
  try {
    const params = new URLSearchParams(new FormData(event.currentTarget));
    const weather = await api(`/api/weather?${params}`);
    $("weather-output").textContent =
      `${weather.temperature} °C · ${weather.humidity}% humidity · ${weather.precipitation} mm current precipitation. As of ${weather.observed_at} (${weather.timezone}). Source: Open-Meteo. Context only; model inputs unchanged.`;
  } catch (error) {
    $("weather-output").textContent = error.message;
    $("weather-output").classList.add("error");
  } finally {
    $("weather-button").disabled = false;
  }
});
async function init() {
  try {
    const [health, info, coverage] = await Promise.all([
      api("/api/health"),
      api("/api/model-info"),
      api("/api/coverage"),
    ]);
    $("health").textContent = health.models_loaded
      ? "Models ready"
      : "Unavailable";
    $("accuracy").textContent =
      `${(info.metrics.classification.test.top1 * 100).toFixed(2)}%`;
    $("r2").textContent = info.metrics.regression.test.r2.toFixed(2);
    options($("state"), coverage.states, "Choose state");
    const scores = info.metrics.regression.test;
    $("model-details").append(
      node(
        "p",
        `Crop test: 440 records, ${(info.metrics.classification.test.top1 * 100).toFixed(2)}% accuracy. Yield test: 2,275 records from 2011–2012. MAE ${scores.mae.toFixed(3)} t/ha, RMSE ${scores.rmse.toFixed(3)} t/ha, R² ${scores.r2.toFixed(3)}.`,
      ),
    );
    for (const limitation of info.limitations)
      $("model-details").append(node("p", limitation));
    status("Ready. Enter measured inputs or load the historical demo.");
  } catch (error) {
    $("health").textContent = "Connection unavailable";
    $("health").classList.add("offline");
    status(error.message, true);
  }
}
init();
