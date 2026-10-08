"""Official MCP SDK server. Stdout is reserved exclusively for protocol traffic."""

import logging
from typing import Any
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import catalog
from .inference import predict_crop_and_yield as predict
from .schemas import PredictionRequest
from .weather import get_live_weather as weather

mcp = FastMCP(
    "AgroIntel",
    instructions="Use measured soil/weather inputs. Query coverage before prediction. Ask for missing inputs rather than inventing them. Always report warnings and distinguish benchmark suitability from farm success. Weather is context only.",
)
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
LOGGER = logging.getLogger(__name__)


@mcp.tool(annotations=READ_ONLY)
def predict_crop_and_yield(request: PredictionRequest, explain: bool = True) -> dict[str, Any]:
    """Rank three crops and estimate historical regional yield where supported. Returns local sensitivity and limitations. No retraining."""
    return predict(request.model_dump(), explain=explain)


@mcp.tool(annotations=READ_ONLY)
def get_model_info() -> dict[str, Any]:
    """Get dataset scope, units, held-out metrics and limitations before advising."""
    return catalog.get_model_info()


@mcp.tool(annotations=READ_ONLY)
def list_supported_locations(
    state: str = "", district: str = "", season: str = ""
) -> dict[str, Any]:
    """List historical states, districts, seasons and crop coverage. Empty filters list all options."""
    return catalog.list_supported_locations(state, district, season)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=False, openWorldHint=True
    )
)
def get_live_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """Fetch optional current weather. Sends coordinates to Open-Meteo; not a replacement for benchmark rainfall."""
    return weather(latitude, longitude)


def main():
    # Warm-load libraries before entering stdio's background reader/writer threads.
    from .inference import artifacts

    artifacts()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
