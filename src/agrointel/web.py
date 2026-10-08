"""Local-first REST service and accessible, dependency-free browser interface."""

import argparse
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .catalog import get_model_info, list_supported_locations
from .config import ROOT
from .inference import artifacts, predict_crop_and_yield
from .schemas import PredictionRequest
from .weather import WeatherUnavailable, get_live_weather

LOGGER = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app):
    artifacts()  # Fail startup if saved model integrity checks fail.
    yield


app = FastAPI(title="AgroIntel", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]", "testserver"]
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        return JSONResponse({"detail": "Cross-origin requests are not supported"}, status_code=403)
    if request.method == "POST":
        if not request.headers.get("content-type", "").lower().startswith("application/json"):
            return JSONResponse({"detail": "Expected application/json"}, status_code=415)
        # Count actual chunks, not just an untrusted Content-Length header.
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 16_384:
                return JSONResponse({"detail": "Request too large"}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/docs", include_in_schema=False)
def api_docs():
    return FileResponse(STATIC / "api.html")


@app.get("/api/health")
def health():
    artifacts()
    return {"status": "ok", "version": "1.0.0", "models_loaded": True}


@app.get("/api/model-info")
def model_info():
    return get_model_info()


@app.get("/api/coverage")
def coverage(
    state: str = Query("", max_length=120),
    district: str = Query("", max_length=120),
    season: str = Query("", max_length=120),
):
    return list_supported_locations(state, district, season)


@app.get("/api/example")
def example():
    import json

    return json.loads((ROOT / "examples/request.json").read_text(encoding="utf-8"))


@app.post("/api/predict")
def predict(request: PredictionRequest, explain: bool = True):
    try:
        return predict_crop_and_yield(request.model_dump(), explain=explain)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except (OSError, RuntimeError) as exc:
        LOGGER.exception("Prediction failed")
        raise HTTPException(503, "Model service unavailable; check server logs") from exc


@app.get("/api/weather")
def weather(
    latitude: float = Query(ge=-90, le=90, allow_inf_nan=False),
    longitude: float = Query(ge=-180, le=180, allow_inf_nan=False),
):
    try:
        return get_live_weather(latitude, longitude)
    except WeatherUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


app.mount("/static", StaticFiles(directory=STATIC), name="static")


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Start AgroIntel's local dashboard")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("agrointel.web:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
