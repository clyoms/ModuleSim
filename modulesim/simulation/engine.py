"""The simulation engine (Built): holds each company and does every sum.

Interface:
    check_company(data) -> list of problems
    check_event(student_id, event) -> list of problems
    load_company(student_id, data)  store a checked company
    get_company(student_id) -> CompanyView (a read-only summary)
    apply_event(student_id, event) -> CompanyView
    apply_decision(student_id, response_id) -> dict (the result)
    current_event(student_id) -> dict or None

The AI never changes a number directly. It suggests figures, the rules in
rules.py check them, and this engine applies them and recalculates the
budget, the end date and the critical path.
"""

import copy
from dataclasses import dataclass

from .cpm import Schedule, critical_path
from .rules import company_problems, event_problems


class RejectedData(ValueError):
    """The AI's figures broke a rule. The message lists every problem."""


@dataclass(frozen=True)
class CompanyView:
    name: str
    brief: str
    project: str
    budget: int
    planned_cost: int
    extra_cost: int
    cost_of_delay_per_week: int
    team: list
    business_case: str
    tasks: list           # task dicts with es, ef, float and critical added
    length: int           # current end week
    baseline_length: int  # end week when the company was created
    critical_paths: list
    source: str           # "ai" or "stored"


@dataclass
class _State:
    company: dict
    baseline_length: int
    extra_cost: int = 0
    event: dict | None = None
    length_after_event: int | None = None


def _schedule(tasks: list[dict]) -> Schedule:
    return critical_path({t["id"]: t["duration"] for t in tasks},
                         {t["id"]: t.get("after", []) for t in tasks})


class SimulationEngine:
    def __init__(self) -> None:
        self._states: dict[str, _State] = {}

    # Checks (used by Scenario before it hands data over)

    def check_company(self, data: dict) -> list[str]:
        return company_problems(data)

    def check_event(self, student_id: str, event: dict) -> list[str]:
        state = self._state(student_id)
        tasks = {t["id"]: t for t in state.company["tasks"]}
        return event_problems(tasks, _schedule(state.company["tasks"]).length, event)

    # Changes

    def load_company(self, student_id: str, data: dict) -> CompanyView:
        problems = self.check_company(data)
        if problems:
            raise RejectedData("; ".join(problems))
        company = copy.deepcopy(data)
        self._states[student_id] = _State(company, _schedule(company["tasks"]).length)
        return self.get_company(student_id)

    def apply_event(self, student_id: str, event: dict) -> CompanyView:
        problems = self.check_event(student_id, event)
        if problems:
            raise RejectedData("; ".join(problems))
        state = self._state(student_id)
        self._task(state, event["task_id"])["duration"] += event["delay"]
        state.event = copy.deepcopy(event)
        state.length_after_event = _schedule(state.company["tasks"]).length
        return self.get_company(student_id)

    def apply_decision(self, student_id: str, response_id: str) -> dict:
        state = self._state(student_id)
        if state.event is None:
            raise RejectedData("There is no event to respond to")
        responses = {r["id"]: r for r in state.event["responses"]}
        if response_id not in responses:
            raise RejectedData(f"Unknown response: {response_id!r}")
        response = responses[response_id]

        before = _schedule(state.company["tasks"])
        self._task(state, response["task_id"])["duration"] -= response["time_saved"]
        state.extra_cost += response["cost"]
        after = _schedule(state.company["tasks"])

        delay_cost_per_week = state.company["business_case"]["cost_of_delay_per_week"]
        weeks_late = max(0, after.length - state.baseline_length)
        planned = sum(t["cost"] for t in state.company["tasks"])
        total_cost = planned + state.extra_cost + weeks_late * delay_cost_per_week

        result = {
            "event_title": state.event["title"],
            "event_task": state.event["task_id"],
            "response_id": response_id,
            "response_note": response.get("note", ""),
            "response_task": response["task_id"],
            "response_cost": response["cost"],
            "time_saved_on_task": response["time_saved"],
            "baseline_end": state.baseline_length,
            "end_after_event": before.length,
            "end_after_decision": after.length,
            "weeks_late": weeks_late,
            "weeks_recovered": before.length - after.length,
            "critical_paths_after": after.critical_paths,
            "response_task_was_critical": before.float[response["task_id"]] == 0,
            "delay_cost": weeks_late * delay_cost_per_week,
            "total_cost": total_cost,
            "budget": state.company["budget"],
            "over_budget_by": max(0, total_cost - state.company["budget"]),
        }
        state.event = None
        return result

    # Reads

    def has_company(self, student_id: str) -> bool:
        return student_id in self._states

    def current_event(self, student_id: str) -> dict | None:
        event = self._state(student_id).event
        return copy.deepcopy(event) if event else None

    def get_company(self, student_id: str) -> CompanyView:
        state = self._state(student_id)
        c = state.company
        schedule = _schedule(c["tasks"])
        tasks = [
            {**t, "es": schedule.es[t["id"]], "ef": schedule.ef[t["id"]],
             "float": schedule.float[t["id"]], "critical": schedule.float[t["id"]] == 0}
            for t in c["tasks"]
        ]
        return CompanyView(
            name=c["name"], brief=c.get("brief", ""), project=c.get("project", ""),
            budget=c["budget"], planned_cost=sum(t["cost"] for t in c["tasks"]),
            extra_cost=state.extra_cost,
            cost_of_delay_per_week=c["business_case"]["cost_of_delay_per_week"],
            team=copy.deepcopy(c.get("team", [])),
            business_case=c["business_case"].get("summary", ""),
            tasks=tasks, length=schedule.length, baseline_length=state.baseline_length,
            critical_paths=schedule.critical_paths, source=c.get("source", "ai"),
        )

    # Helpers

    def _state(self, student_id: str) -> _State:
        if student_id not in self._states:
            raise KeyError(f"No company for student {student_id!r}")
        return self._states[student_id]

    @staticmethod
    def _task(state: _State, task_id: str) -> dict:
        return next(t for t in state.company["tasks"] if t["id"] == task_id)
