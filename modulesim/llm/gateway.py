"""The AI gateway: the one route to any AI model (Built).

Interface:
    AIGateway.complete(task, instructions, data, schema) -> dict

What it does on every call (Part 1, Risk 7):
1. Removes emails and student numbers from the data (Risk 3).
2. Tries the first provider with a time limit (20 seconds by default).
3. Checks the answer has the right shape. A wrong shape counts as a failure.
4. On failure, tries the same provider once more (one retry).
5. Then moves to the next provider in the list.
6. If every provider fails, raises AIUnavailable. The caller then uses its
   stored fallback, so the student sees a plain message and no crash.

Swapping Gemini for another provider means changing the provider list in
wiring.py. No other package changes.
"""

import concurrent.futures
from dataclasses import dataclass, field

from .checks import redact_data, shape_problems
from .client import AIUnavailable, LLMClient, LLMError


@dataclass
class CallRecord:
    provider: str
    task: str
    ok: bool
    detail: str = ""


@dataclass
class AIGateway:
    providers: list[LLMClient]
    timeout: float = 20.0
    retries: int = 1
    calls: list[CallRecord] = field(default_factory=list)

    def complete(self, task: str, instructions: str, data: dict, schema: dict) -> dict:
        safe_data = redact_data(data)
        for provider in self.providers:
            for _attempt in range(1 + self.retries):
                try:
                    answer = self._call_with_timeout(
                        provider, task, instructions, safe_data, schema
                    )
                except LLMError as error:
                    self.calls.append(CallRecord(provider.name, task, False, str(error)))
                    continue
                problems = shape_problems(answer, schema)
                if problems:
                    self.calls.append(
                        CallRecord(provider.name, task, False, "; ".join(problems[:3]))
                    )
                    continue
                self.calls.append(CallRecord(provider.name, task, True))
                return answer
        raise AIUnavailable(f"No AI provider could complete the {task!r} task")

    def _call_with_timeout(self, provider, task, instructions, data, schema) -> dict:
        # The thread makes sure even a provider that ignores its own timeout
        # cannot hold the student's page for longer than the limit.
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = pool.submit(
            provider.complete, task, instructions, data, schema, self.timeout
        )
        try:
            return future.result(timeout=self.timeout)
        except concurrent.futures.TimeoutError as error:
            raise LLMError(f"{provider.name} timed out after {self.timeout}s") from error
        except LLMError:
            raise
        except Exception as error:  # any other provider bug counts as a failure
            raise LLMError(f"{provider.name} failed: {error}") from error
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
