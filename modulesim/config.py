"""Settings, read from the environment or a private .env file.

The .env file is listed in .gitignore, so the API key never reaches the
repository (Part 1, Risk 2). See .env.example for every setting.
"""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines into the environment. Real settings win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Config:
    ai_provider: str = "mock"          # "mock" or "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    ai_timeout: float = 20.0
    database: str = str(ROOT / "instance" / "modulesim.db")
    secret_key: str = "dev-only-change-me"

    @classmethod
    def from_environment(cls) -> "Config":
        load_dotenv()
        return cls(
            ai_provider=os.environ.get("AI_PROVIDER", "mock").lower(),
            gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
            gemini_model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
            ai_timeout=float(os.environ.get("AI_TIMEOUT", "20")),
            database=os.environ.get("DATABASE", str(ROOT / "instance" / "modulesim.db")),
            secret_key=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        )
