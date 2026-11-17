"""Wiring: builds every component and connects them through the event bus.

This is the only file that knows about all the components. Reading the
subscriptions below, top to bottom, gives the Part 1 data flow for one month:

    1. COMPANY_REQUESTED  -> Scenario creates a company
       COMPANY_CREATED    -> Simulation engine checks and stores it
    2. MONTH_STARTED      -> Scenario writes the month's event from the notes
       EVENT_READY        -> Simulation engine checks and applies it
    3. DECISION_SUBMITTED -> Simulation engine applies the response figures
       RESULT_READY       -> Feedback marker explains and marks the reasoning
       FEEDBACK_READY     -> Progress records the attempt

Moving to the target design means each handler becomes a separate service
listening on a real queue. The handlers and message names stay the same.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .config import Config
from .content import ContentStore
from .events import EventBus, messages as m
from .feedback import FeedbackMarker
from .identity import DemoIdentity
from .llm import AIGateway
from .llm.mock import MockClient
from .progress import ProgressStore
from .scenario import ScenarioGenerator
from .simulation import SimulationEngine


@dataclass
class System:
    bus: EventBus
    gateway: AIGateway
    content: ContentStore
    engine: SimulationEngine
    scenario: ScenarioGenerator
    marker: FeedbackMarker
    progress: ProgressStore
    identity: DemoIdentity
    notices: dict = field(default_factory=dict)  # student id -> message for the screen


def build_providers(config: Config) -> list:
    """The only place that chooses an AI provider."""
    if config.ai_provider == "gemini":
        from .llm.gemini import GeminiClient
        return [GeminiClient(config.gemini_api_key, config.gemini_model)]
    return [MockClient()]


def build_system(config: Config, providers: list | None = None) -> System:
    if config.database != ":memory:":
        Path(config.database).parent.mkdir(parents=True, exist_ok=True)

    bus = EventBus()
    gateway = AIGateway(providers if providers is not None else build_providers(config),
                        timeout=config.ai_timeout)
    content = ContentStore()
    engine = SimulationEngine()
    system = System(
        bus=bus, gateway=gateway, content=content, engine=engine,
        scenario=ScenarioGenerator(gateway, content, engine),
        marker=FeedbackMarker(gateway, content),
        progress=ProgressStore(config.database),
        identity=DemoIdentity(),
    )
    _subscribe(system)
    return system


def _notice(system: System, student_id: str, item: dict) -> None:
    if item.get("source") == "stored":
        system.notices[student_id] = (
            "The AI is unavailable right now, so you are playing a stored practice scenario."
        )


def _subscribe(s: System) -> None:
    bus = s.bus

    # 1. Company
    def create_company(msg):
        company = s.scenario.create_company(msg["module"])
        _notice(s, msg["student_id"], company)
        bus.publish(m.COMPANY_CREATED, {**msg, "company": company})

    def store_company(msg):
        s.engine.load_company(msg["student_id"], msg["company"])

    bus.subscribe(m.COMPANY_REQUESTED, create_company)
    bus.subscribe(m.COMPANY_CREATED, store_company)

    # 2. Month event
    def write_event(msg):
        event = s.scenario.next_event(msg["student_id"], msg["module"])
        _notice(s, msg["student_id"], event)
        bus.publish(m.EVENT_READY, {**msg, "event": event})

    def apply_event(msg):
        s.engine.apply_event(msg["student_id"], msg["event"])
        bus.publish(m.STATE_UPDATED, {"student_id": msg["student_id"]})

    bus.subscribe(m.MONTH_STARTED, write_event)
    bus.subscribe(m.EVENT_READY, apply_event)

    # 3. Decision, feedback and progress
    def apply_decision(msg):
        result = s.engine.apply_decision(msg["student_id"], msg["response_id"])
        bus.publish(m.RESULT_READY, {**msg, "result": result})

    def mark(msg):
        feedback = s.marker.mark(msg["result"], msg["reasoning"], msg["module"])
        bus.publish(m.FEEDBACK_READY, {**msg, "feedback": feedback})

    def record(msg):
        topics = sorted({p["source_title"] for p in
                         msg["feedback"]["good_points"] + msg["feedback"]["missed_points"]})
        attempt_id = s.progress.save_attempt({**msg, "topics": topics})
        bus.publish(m.ATTEMPT_SAVED, {"student_id": msg["student_id"], "attempt_id": attempt_id})

    bus.subscribe(m.DECISION_SUBMITTED, apply_decision)
    bus.subscribe(m.RESULT_READY, mark)
    bus.subscribe(m.FEEDBACK_READY, record)
