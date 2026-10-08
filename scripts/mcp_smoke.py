"""Run the actual MCP server as a client would, and save reproducible evidence."""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def run():
    server = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "scripts/run_mcp.py")], cwd=str(ROOT)
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            request = json.loads((ROOT / "examples/request.json").read_text())
            result = await session.call_tool("predict_crop_and_yield", {"request": request})
            if result.isError:
                raise RuntimeError(str(result.content))
            evidence = {
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "transport": "stdio",
                "tools": [tool.name for tool in tools.tools],
                "prediction": result.structuredContent,
            }
            (ROOT / "reports/mcp_smoke.json").write_text(
                json.dumps(evidence, indent=2), encoding="utf-8"
            )
            print(
                json.dumps(
                    {
                        "tools": evidence["tools"],
                        "top_crop": evidence["prediction"]["recommendations"][0]["crop"],
                    },
                    indent=2,
                )
            )


if __name__ == "__main__":
    asyncio.run(run())
