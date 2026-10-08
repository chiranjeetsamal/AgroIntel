"""Package code, trained artifacts and reports without data or environments."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT.parent / "AgroIntel_Complete_Project.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(
                part
                in {
                    ".git",
                    ".venv",
                    "__pycache__",
                    ".pytest_cache",
                    ".ruff_cache",
                    "dist",
                    "build",
                    "raw",
                    "processed",
                }
                or part.endswith(".egg-info")
                for part in relative.parts
            ):
                continue
            if path.name == ".env" or path.suffix in {".zip", ".log", ".pyc"}:
                continue
            archive.write(path, Path("agrointel") / relative)
    print(output)


if __name__ == "__main__":
    main()
