"""Architecture checks: components talk only through each other's interfaces.

A package may import another package (from ..simulation import X), but not
reach into its inside files (from ..simulation.engine import X). Only
wiring.py may pick an AI provider, and only the llm package may talk to one.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "modulesim"
PACKAGES = {"events", "llm", "simulation", "content", "scenario",
            "feedback", "progress", "identity", "web"}


def imports_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = path.relative_to(ROOT).parts[0]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level >= 1:
            if node.level == 1 and path.parent != ROOT:
                continue  # a file importing from its own package is fine
            found.append(node.module or "")
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("modulesim."):
            found.append(node.module.removeprefix("modulesim."))
        elif isinstance(node, ast.Import):
            found += [a.name.removeprefix("modulesim.") for a in node.names
                      if a.name.startswith("modulesim.")]
    return [f for f in found if f.split(".")[0] in PACKAGES and f.split(".")[0] != package]


def package_files():
    for pkg in PACKAGES:
        yield from (ROOT / pkg).rglob("*.py")


def test_no_package_reaches_into_another_packages_inside_files():
    offences = []
    for path in package_files():
        for target in imports_in(path):
            if "." in target:
                offences.append(f"{path.relative_to(ROOT)} imports {target}")
    assert offences == []


def test_only_the_llm_package_and_wiring_know_about_ai_providers():
    offences = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == "llm" or rel.name == "wiring.py":
            continue
        text = path.read_text(encoding="utf-8")
        for word in ("GeminiClient", "MockClient", "urllib.request", "generativelanguage"):
            if word in text:
                offences.append(f"{rel} mentions {word}")
    assert offences == []


def test_every_component_package_exists():
    for pkg in PACKAGES:
        assert (ROOT / pkg / "__init__.py").exists(), pkg
