"""Scan the project for API keys before a submission (Part 1, Risk 2).

Run from the project folder:  python scripts/check_secrets.py
Or check a finished zip:      python scripts/check_secrets.py ModuleSim.zip

It looks for Google API keys (they start with "AIza"), other common key
shapes, and any .env file. It exits with an error if it finds one.
"""

import re
import sys
import zipfile
from pathlib import Path

PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "Groq API key": re.compile(r"gsk_[0-9A-Za-z]{20,}"),
    "Anthropic API key": re.compile(r"sk-ant-[0-9A-Za-z_\-]{20,}"),
    "key written into a setting": re.compile(r"GEMINI_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}"),
}
SKIP_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "instance"}


def scan_text(name: str, text: str) -> list[str]:
    return [f"{name}: looks like a {label}" for label, rx in PATTERNS.items() if rx.search(text)]


def scan_folder(root: Path) -> list[str]:
    found = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts) or not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if path.name == ".env":
            found.append(f"{rel}: a .env file must not be submitted")
            continue
        try:
            found += scan_text(rel, path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            pass
    return found


def scan_zip(path: Path) -> list[str]:
    found = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if Path(name).name == ".env":
                found.append(f"{name}: a .env file must not be submitted")
                continue
            try:
                found += scan_text(name, z.read(name).decode("utf-8"))
            except UnicodeDecodeError:
                pass
    return found


def main(argv: list[str]) -> int:
    target = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    found = scan_zip(target) if target.suffix == ".zip" else scan_folder(target)
    for line in found:
        print("FOUND", line)
    print("No keys found." if not found else f"{len(found)} problem(s). Remove them before you submit.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
