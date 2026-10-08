"""REST, validation, local explanation and deterministic weather failure tests."""

import json
import math
from unittest.mock import Mock

import pytest
import requests
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agrointel.config import ROOT
from agrointel.inference import predict_crop_and_yield
from agrointel.schemas import PredictionRequest
from agrointel.web import app
from agrointel.weather import WeatherUnavailable, get_live_weather


@pytest.fixture
def request_data():
    return json.loads((ROOT / "examples/request.json").read_text())


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as session:
        yield session


def test_dashboard_health_assets(client):
    assert client.get("/api/health").json()["models_loaded"]
    index = client.get("/")
    assert "What could grow" in index.text
    assert "frame-ancestors 'none'" in index.headers["content-security-policy"]
    for path in ("styles.css", "app.js"):
        assert client.get(f"/static/{path}").status_code == 200
    assert "Try a prediction" in client.get("/docs").text
    assert "/api/predict" in client.get("/openapi.json").json()["paths"]
    assert client.get("/static/../../artifacts/metadata.json").status_code == 404


def test_api_matches_python(client, request_data):
    response = client.post("/api/predict", json=request_data)
    assert response.status_code == 200
    expected = predict_crop_and_yield(request_data)
    actual = response.json()
    assert actual["recommendations"][0]["crop"] == expected["recommendations"][0]["crop"]
    assert actual["recommendations"][0]["estimated_yield"] == pytest.approx(
        expected["recommendations"][0]["estimated_yield"]
    )
    assert len(actual["recommendations"][0]["explanation"]["features"]) == 7
    json.dumps(actual, allow_nan=False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("nitrogen", True),
        ("rainfall", "20"),
        ("year", 2010.0),
        ("year", 2010.5),
        ("humidity", 101),
        ("area", 0),
        ("state", " "),
    ],
)
def test_strict_requests(client, request_data, field, value):
    request_data[field] = value
    assert client.post("/api/predict", json=request_data).status_code == 422


def test_unknown_and_missing_fields(client, request_data):
    request_data["production"] = 123
    assert client.post("/api/predict", json=request_data).status_code == 422
    del request_data["production"]
    del request_data["humidity"]
    assert client.post("/api/predict", json=request_data).status_code == 422


def test_nonfinite_and_normalisation(request_data):
    for value in (math.inf, math.nan, -math.inf):
        with pytest.raises(ValidationError):
            PredictionRequest.model_validate({**request_data, "area": value})
    request_data["district"] = " ADILABAD  "
    assert PredictionRequest.model_validate(request_data).district == "adilabad"


def test_security(client, request_data):
    assert (
        client.post(
            "/api/predict", json=request_data, headers={"Origin": "https://untrusted.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/predict", content="x" * 17_000, headers={"Content-Type": "application/json"}
        ).status_code
        == 413
    )
    assert client.post("/api/predict", data=request_data).status_code == 415
    assert client.get("/api/health", headers={"Host": "untrusted.example"}).status_code == 400
    assert (
        client.post(
            "/api/predict", json=request_data, headers={"Origin": "http://testserver"}
        ).status_code
        == 200
    )


def test_model_info_coverage_and_example(client, request_data):
    info = client.get("/api/model-info").json()
    assert len(info["crop_classes"]) == 22
    assert info["metrics"]["classification"]["test"]["top1"] > 0.99
    coverage = client.get(
        "/api/coverage",
        params={"state": request_data["state"], "district": request_data["district"]},
    ).json()
    assert request_data["season"] in coverage["seasons"]
    assert client.get("/api/coverage?state=unknown").json()["matching_combinations"] == 0
    assert client.get("/api/example").json() == request_data


def test_explanation_math(request_data):
    import pandas as pd
    from agrointel.inference import artifacts
    from agrointel.config import CFEATURES

    result = predict_crop_and_yield(request_data)
    classifier, _, _ = artifacts()
    best = result["recommendations"][0]
    first = best["explanation"]["features"][0]
    row = dict(
        zip(
            CFEATURES,
            [
                request_data[k]
                for k in (
                    "nitrogen",
                    "phosphorus",
                    "potassium",
                    "temperature",
                    "humidity",
                    "ph",
                    "rainfall",
                )
            ],
        )
    )
    row[first["feature"]] = first["reference"]
    index = list(classifier.classes_).index(best["crop"])
    probe = classifier.predict_proba(pd.DataFrame([row], columns=CFEATURES))[0, index]
    assert first["probability_delta"] == pytest.approx(best["suitability_probability"] - probe)
    assert predict_crop_and_yield(request_data, explain=False)["recommendations"][0][
        "explanation"
    ] == {"status": "disabled"}


@pytest.mark.parametrize("latitude,longitude", [(91, 0), (0, 181), (True, 0), (math.nan, 0)])
def test_bad_weather_coordinates(latitude, longitude):
    with pytest.raises(ValueError):
        get_live_weather(latitude, longitude)


def test_weather_success_and_failure(monkeypatch, client):
    response = Mock()
    response.json.return_value = {
        "current": {
            "temperature_2m": 25,
            "relative_humidity_2m": 60,
            "precipitation": 0,
            "time": "2026-10-08T10:00",
        },
        "current_units": {
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "precipitation": "mm",
        },
        "timezone": "Asia/Kolkata",
    }
    monkeypatch.setattr("agrointel.weather.requests.get", Mock(return_value=response))
    assert get_live_weather(12.97, 77.59)["temperature"] == 25
    assert client.get("/api/weather?latitude=12.97&longitude=77.59").status_code == 200
    assert client.get("/api/weather?latitude=91&longitude=0").status_code == 422
    monkeypatch.setattr("agrointel.weather.requests.get", Mock(side_effect=requests.Timeout()))
    with pytest.raises(WeatherUnavailable):
        get_live_weather(0, 0)
    assert client.get("/api/weather?latitude=0&longitude=0").status_code == 503
    response.json.return_value = {"current": {}}
    monkeypatch.setattr("agrointel.weather.requests.get", Mock(return_value=response))
    with pytest.raises(WeatherUnavailable):
        get_live_weather(0, 0)
