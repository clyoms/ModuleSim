"""The mock AI client: realistic fake answers through the same interface.

It is the default provider, so the app and every test run with no key, no
internet and no cost. It follows the LLMClient interface exactly, which is
why swapping it for Gemini is a change in one place (wiring.py).

The mock always plays the Harbour Coffee Co. company from the Part 1
wireframes. Tests can replace any answer with `script`.
"""

import copy
import re

HARBOUR_COFFEE = {
    "name": "Harbour Coffee Co.",
    "brief": (
        "A small chain of four Cork cafes. Queues at peak times lose sales, so "
        "the owners want customers to order and pay on their phones."
    ),
    "project": "Mobile ordering and new tills in all four cafes",
    "budget": 60000,
    "team": [
        {"name": "Aoife", "role": "Project manager (you)"},
        {"name": "Tomas", "role": "App developer"},
        {"name": "Niamh", "role": "Cafe operations lead"},
        {"name": "Supplier", "role": "Till and tablet supplier"},
    ],
    "business_case": {
        "summary": (
            "Mobile ordering should cut peak queues and win back lost sales. "
            "Every week the launch slips costs about EUR 4,000 in lost sales."
        ),
        "cost_of_delay_per_week": 4000,
    },
    "tasks": [
        {"id": "A", "name": "Agree requirements with cafe managers", "duration": 1, "cost": 2000, "after": []},
        {"id": "B", "name": "Order tills and tablets from supplier", "duration": 3, "cost": 18000, "after": ["A"]},
        {"id": "C", "name": "Build the ordering app", "duration": 4, "cost": 16000, "after": ["A"]},
        {"id": "D", "name": "Install hardware in the cafes", "duration": 3, "cost": 9000, "after": ["B"]},
        {"id": "E", "name": "Connect the app to the tills", "duration": 1, "cost": 4000, "after": ["C", "D"]},
        {"id": "F", "name": "Train cafe staff", "duration": 1, "cost": 3000, "after": ["D"]},
        {"id": "G", "name": "Go live", "duration": 1, "cost": 2000, "after": ["E", "F"]},
    ],
}

SUPPLIER_DELAY_EVENT = {
    "title": "Your hardware supplier is two weeks late",
    "description": (
        "The supplier has written to say the tills and tablets will arrive two "
        "weeks late. Installation cannot start until they arrive."
    ),
    "task_id": "B",
    "delay": 2,
    "responses": [
        {"id": "crash", "task_id": "D", "cost": 3000, "time_saved": 1,
         "note": "Pay the installers overtime to fit the hardware a week faster."},
        {"id": "fast_track", "task_id": "D", "cost": 2000, "time_saved": 1,
         "note": "Start connecting the app in the first cafe while the others are still being fitted. Risk of rework."},
        {"id": "re_sequence", "task_id": "C", "cost": 0, "time_saved": 1,
         "note": "Move the app work around so it finishes a week earlier."},
        {"id": "reduce_scope", "task_id": "D", "cost": 4000, "time_saved": 1,
         "note": "Go live in three cafes first. The fourth cafe's lost sales count as the cost."},
        {"id": "escalate", "task_id": "B", "cost": 0, "time_saved": 0,
         "note": "Raise an issue with the owners and ask them to choose: more money or a later date."},
        {"id": "accept", "task_id": "B", "cost": 0, "time_saved": 0,
         "note": "Accept the delay and move the go-live date."},
    ],
}

BANDS = ["First (70+)", "2.1 (60-69)", "2.2 (50-59)", "Third (40-49)", "Fail (below 40)"]

# Ideas the mock marker looks for in the student's reasoning, and the words
# to find the matching passage in the notes.
_CONCEPTS = {
    "critical path": ["critical path", "critical"],
    "float": ["float", "slack"],
    "crashing": ["crash", "overtime", "adding people"],
    "tolerance": ["tolerance", "escalat"],
    "business case": ["business case", "cost of delay", "benefit"],
    "dependencies": ["depend", "merge", "overlap"],
}


def _first_sentence(text: str) -> str:
    match = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return match.group(1) if match else text.strip()


class MockClient:
    name = "mock"

    def __init__(self, script: dict | None = None):
        # script maps a task name to a fixed answer, or to a function that
        # takes (instructions, data) and returns an answer.
        self.script = script or {}

    def complete(self, task, instructions, data, schema, timeout):
        if task in self.script:
            answer = self.script[task]
            return answer(instructions, data) if callable(answer) else copy.deepcopy(answer)
        if task == "company":
            return copy.deepcopy(HARBOUR_COFFEE)
        if task == "event":
            return copy.deepcopy(SUPPLIER_DELAY_EVENT)
        if task == "feedback":
            return self._feedback(data)
        raise ValueError(f"Mock has no answer for task {task!r}")

    def _feedback(self, data: dict) -> dict:
        reasoning = data.get("reasoning", "").lower()
        passages = data.get("passages", [])
        result = data.get("result", {})

        used = [c for c, words in _CONCEPTS.items() if any(w in reasoning for w in words)]
        band = BANDS[max(0, 4 - len(used))] if used else BANDS[4]

        cited: set[str] = set()

        def cite(concept: str) -> dict | None:
            # The passage that mentions the idea most, not used yet.
            def hits(p):
                return sum(p["text"].lower().count(w) for w in _CONCEPTS[concept])
            options = [p for p in passages if p["id"] not in cited and hits(p)]
            if not options:
                return None
            best = max(options, key=hits)
            cited.add(best["id"])
            return {"passage_id": best["id"], "quote": _first_sentence(best["text"])}

        good, missed = [], []
        for concept in used:
            source = cite(concept)
            if source:
                good.append({"text": f"You used the idea of {concept} to justify your choice.", **source})
        if "critical path" not in used:
            source = cite("critical path")
            if source:
                missed.append({"text": "Check whether the delayed task is on the critical path before you choose.", **source})

        before = result.get("end_after_event")
        after = result.get("end_after_decision")
        return {
            "summary": (
                f"After your decision the project now ends in week {after}, "
                f"against week {before} after the delay."
            ),
            "forecast": (
                "If later tasks slip as well, the go-live date will move again, "
                "because the remaining tasks on the critical path have no float."
            ),
            "band": band,
            "good_points": good,
            "missed_points": missed,
        }
