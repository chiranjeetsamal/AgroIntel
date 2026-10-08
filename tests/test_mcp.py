"""Real subprocess test of initialize, tools/list and tools/call over stdio."""

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agrointel.config import ROOT


def test_stdio_end_to_end():
    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=[str(ROOT / "scripts/run_mcp.py")], cwd=str(ROOT)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {tool.name for tool in tools.tools} == {
                    "predict_crop_and_yield",
                    "get_model_info",
                    "list_supported_locations",
                    "get_live_weather",
                }
                info = await session.call_tool("get_model_info", {})
                assert not info.isError
                coverage = await session.call_tool(
                    "list_supported_locations", {"state": "andhra pradesh", "district": "adilabad"}
                )
                assert not coverage.isError
                request = json.loads((ROOT / "examples/request.json").read_text())
                result = await session.call_tool("predict_crop_and_yield", {"request": request})
                assert not result.isError
                structured = result.structuredContent
                assert structured["recommendations"][0]["crop"] == "rice"
                assert structured["recommendations"][0]["estimated_yield"] > 0
                invalid = await session.call_tool(
                    "predict_crop_and_yield", {"request": {**request, "humidity": 200}}
                )
                assert invalid.isError
                unknown = await session.call_tool(
                    "predict_crop_and_yield", {"request": {**request, "district": "unknown"}}
                )
                assert not unknown.isError
                assert all(
                    crop["estimated_yield"] is None
                    for crop in unknown.structuredContent["recommendations"]
                )

    asyncio.run(asyncio.wait_for(run(), timeout=60))
