"""Optional Open-Meteo context; never silently substitutes training inputs."""

import math
from numbers import Real
from datetime import datetime, timezone

import requests


class WeatherUnavailable(RuntimeError):
    pass


def get_live_weather(latitude: float, longitude: float) -> dict:
    for label, value, bound in (("latitude", latitude, 90), ("longitude", longitude, 180)):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            or not -bound <= value <= bound
        ):
            raise ValueError(f"{label} must be a finite number within +/-{bound}")
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=(3, 8),
        )
        response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        units = payload["current_units"]
        for key in ("temperature_2m", "relative_humidity_2m", "precipitation"):
            value = current[key]
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
                raise ValueError("Invalid weather measurement")
        if not isinstance(current["time"], str):
            raise ValueError("Invalid weather timestamp")
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise WeatherUnavailable(
            "Live weather is unavailable. Manual model inputs still work; try again later."
        ) from exc
    return {
        "source": "Open-Meteo",
        "source_url": "https://open-meteo.com/",
        "requested_coordinates": {"latitude": latitude, "longitude": longitude},
        "timezone": payload.get("timezone", "unknown"),
        "observed_at": current["time"],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "precipitation": current["precipitation"],
        "units": units,
        "warning": "Current modeled weather is contextual only. It is not a seasonal forecast or the benchmark rainfall input. Values are not applied to model inputs automatically.",
    }
