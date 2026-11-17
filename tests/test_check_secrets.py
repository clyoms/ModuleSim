"""Tests for the key scan (Part 1, Risk 2)."""

import importlib.util
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_secrets.py"
spec = importlib.util.spec_from_file_location("check_secrets", SCRIPT)
check_secrets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_secrets)

FAKE_KEY = "AIza" + "x" * 35   # built here so this file never holds a key-shaped string


def test_a_key_in_a_file_is_found(tmp_path):
    (tmp_path / "settings.py").write_text(f'KEY = "{FAKE_KEY}"')
    assert check_secrets.scan_folder(tmp_path)


def test_a_dotenv_file_is_found_in_a_zip(tmp_path):
    archive = tmp_path / "submission.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("ModuleSim/.env", "AI_PROVIDER=gemini")
        z.writestr("ModuleSim/README.md", "hello")
    assert check_secrets.scan_zip(archive) == ["ModuleSim/.env: a .env file must not be submitted"]


def test_the_project_itself_is_clean():
    assert check_secrets.scan_folder(SCRIPT.parent.parent) == []
