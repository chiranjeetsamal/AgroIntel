import math
from numbers import Real
from .data import normalise

NUMBERS = [
    "nitrogen",
    "phosphorus",
    "potassium",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "year",
    "area",
]
TEXT = ["state", "district", "season"]


def validate(request):
    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")
    extra = set(request) - set(NUMBERS + TEXT)
    if extra:
        raise ValueError(f"Unknown request fields: {', '.join(sorted(map(str, extra)))}")
    out = {}
    for key in NUMBERS:
        value = request.get(key)
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number")
        out[key] = float(value)
    for key in TEXT:
        if (
            not isinstance(request.get(key), str)
            or not request[key].strip()
            or len(request[key]) > 120
        ):
            raise ValueError(f"{key} must be a nonempty string")
        out[key] = normalise(request[key])
    if any(out[k] < 0 for k in ["nitrogen", "phosphorus", "potassium", "rainfall"]):
        raise ValueError("Nutrients and rainfall must be nonnegative")
    if (
        not 0 <= out["humidity"] <= 100
        or not 0 <= out["ph"] <= 14
        or not -50 <= out["temperature"] <= 65
    ):
        raise ValueError("Impossible humidity, pH or temperature")
    if out["area"] <= 0 or not out["year"].is_integer() or not 1900 <= out["year"] <= 2200:
        raise ValueError("Area must be positive and year a valid integer")
    out["year"] = int(out["year"])
    return out
