"""Absolute-path launcher for Codex; independent of its working directory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agrointel.mcp_server import main

if __name__ == "__main__":
    main()
