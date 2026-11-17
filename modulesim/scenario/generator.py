"""Scenario (Built): asks the AI for the company and each month's event.

Interface:
    create_company(module) -> company dict, checked
    next_event(student_id, module) -> event dict, checked

Flow for each request (Part 1, Risk 8):
1. Find the matching passages in Course content.
2. Ask the AI, through the AI gateway, for the company or event.
3. Ask the simulation engine to check every number.
4. If the check fails, ask the AI once more.
5. If it fails again, or no AI is available, use the stored fallback.

Every dict it returns carries "source": "ai" or "stored", so the screen can
tell the student when a stored scenario is in use (Risk 7).
"""

from ..llm import AIUnavailable
from . import stored
from .schemas import COMPANY, EVENT

COMPANY_INSTRUCTIONS = """You design practice scenarios for university students.
Create one fictional small company running one IT project, for the module
named in the data. Use only ideas found in the notes passages.
Rules: 5 to 9 tasks with ids "A", "B", "C" and so on; durations are whole
weeks from 1 to 12; costs are whole euro; "after" lists the ids of the tasks
that must finish first; the budget must cover the total task cost with about
10% to spare; give a weekly cost of delay based on the business case.
Answer with JSON only, in the given schema."""

EVENT_INSTRUCTIONS = """You write one month's problem for a student project manager.
The data holds the company, its tasks with their float, and notes passages.
Write one realistic event that delays exactly one existing task by a whole
number of weeks, no more than the "max_delay" in the data.
Then give figures for each of these six responses, in this order:
crash, fast_track, re_sequence, reduce_scope, escalate, accept.
For each response name the task it changes, its extra cost in whole euro and
the whole weeks it saves on that task, using the business case.
Crashing must cost more and save time. Accept and escalate save no time on
their own, and accepting has no direct cost.
Answer with JSON only, in the given schema."""


class ScenarioGenerator:
    def __init__(self, gateway, content, engine, attempts: int = 2):
        self._gateway = gateway
        self._content = content
        self._engine = engine
        self._attempts = attempts

    def create_company(self, module: str) -> dict:
        data = {"module": module,
                "passages": self._content.search(module, "business case project budget tasks")}
        for _ in range(self._attempts):
            try:
                company = self._gateway.complete("company", COMPANY_INSTRUCTIONS, data, COMPANY)
            except AIUnavailable:
                break
            if not self._engine.check_company(company):
                return {**company, "source": "ai"}
        return {**stored.company(), "source": "stored"}

    def next_event(self, student_id: str, module: str) -> dict:
        view = self._engine.get_company(student_id)
        data = {
            "company": {"name": view.name, "project": view.project,
                        "business_case": view.business_case,
                        "cost_of_delay_per_week": view.cost_of_delay_per_week},
            "tasks": [{k: t[k] for k in ("id", "name", "duration", "cost", "after", "float")}
                      for t in view.tasks],
            "max_delay": stored.max_delay(view.length),
            "passages": self._content.search(module, "critical path float delay crash tolerance"),
        }
        for _ in range(self._attempts):
            try:
                event = self._gateway.complete("event", EVENT_INSTRUCTIONS, data, EVENT)
            except AIUnavailable:
                break
            if not self._engine.check_event(student_id, event):
                return {**event, "source": "ai"}
        event = stored.event_for(view)
        return {**event, "source": "stored"}
