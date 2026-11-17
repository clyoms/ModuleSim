"""One real Gemini call, to check the key and the reply format.

Run it from the project folder after you add your key to .env:
    python scripts/check_gemini.py

It prints the parsed answer, or the error. It never prints the key.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulesim.config import Config  # noqa: E402
from modulesim.llm import AIGateway, AIUnavailable  # noqa: E402
from modulesim.llm.gemini import GeminiClient  # noqa: E402

config = Config.from_environment()
if not config.gemini_api_key:
    sys.exit("No GEMINI_API_KEY in .env. Copy .env.example to .env and add your key.")

gateway = AIGateway([GeminiClient(config.gemini_api_key, config.gemini_model)],
                    timeout=config.ai_timeout)
schema = {"type": "object", "required": ["critical_path", "length"],
          "properties": {"critical_path": {"type": "array", "items": {"type": "string"}},
                         "length": {"type": "integer"}}}
try:
    answer = gateway.complete(
        "check", "Find the critical path and its length in weeks.",
        {"tasks": {"A": {"weeks": 2, "after": []}, "B": {"weeks": 3, "after": ["A"]},
                   "C": {"weeks": 1, "after": ["A"]}, "D": {"weeks": 1, "after": ["B", "C"]}}},
        schema)
except AIUnavailable:
    for call in gateway.calls:
        print(f"  {call.provider}: {call.detail}")
    sys.exit("Gemini did not answer correctly. See the lines above.")

print(f"Gemini ({config.gemini_model}) answered: {answer}")
print("Expected: critical path A, B, D and length 6.")
