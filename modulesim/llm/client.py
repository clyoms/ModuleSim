"""The AI client interface that every provider follows.

Interface:
    complete(task, instructions, data, schema, timeout) -> dict

- task: a short name for the job ("company", "event" or "feedback").
- instructions: what the AI should do, in plain text.
- data: the facts the AI works from (notes, the company, the student's
  reasoning). Data is kept apart from the instructions on purpose: the
  student's text is sent as quoted data, never as an instruction
  (Part 1, Risk 1).
- schema: the shape of the answer, as a small JSON Schema.
- Returns the answer as a Python dict.

Any provider that fails raises LLMError. Nothing outside this package ever
imports a provider directly. Other packages only see AIGateway.
"""

from typing import Protocol


class LLMError(Exception):
    """A provider failed: timeout, network error, bad reply or bad shape."""


class AIUnavailable(Exception):
    """Every provider failed. The caller should use its stored fallback."""


class LLMClient(Protocol):
    name: str

    def complete(
        self, task: str, instructions: str, data: dict, schema: dict, timeout: float
    ) -> dict: ...
