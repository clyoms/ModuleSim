from modulesim.content import ContentStore
from modulesim.llm import AIGateway
from modulesim.llm.mock import MockClient
from modulesim.scenario import ScenarioGenerator
from modulesim.scenario import stored
from modulesim.simulation import SimulationEngine

from conftest import FailingClient, delay_on


def make(script=None, providers=None):
    engine = SimulationEngine()
    gateway = AIGateway(providers or [MockClient(script)], retries=0)
    return ScenarioGenerator(gateway, ContentStore(), engine), engine, gateway


def test_a_valid_ai_company_is_accepted(harbour):
    harbour["name"] = "Lee Valley Bikes"
    scenario, _, _ = make({"company": harbour})
    company = scenario.create_company("IS3328")
    assert company["name"] == "Lee Valley Bikes"
    assert company["source"] == "ai"


def test_a_company_with_impossible_numbers_is_retried_then_replaced(harbour):
    harbour["tasks"][0]["duration"] = -3
    scenario, _, gateway = make({"company": harbour})
    company = scenario.create_company("IS3328")
    assert company["source"] == "stored"
    assert company["name"] == "Harbour Coffee Co."
    assert len(gateway.calls) == 2   # asked once, then once more


def test_the_retry_is_used_when_the_second_answer_is_valid(harbour):
    bad = {**harbour, "budget": 10}
    answers = iter([bad, harbour])
    scenario, _, _ = make({"company": lambda instructions, data: next(answers)})
    assert scenario.create_company("IS3328")["source"] == "ai"


def test_no_ai_means_the_stored_company(harbour):
    scenario, _, _ = make(providers=[FailingClient()])
    assert scenario.create_company("IS3328")["source"] == "stored"


def test_the_ai_is_given_the_notes_passages():
    seen = {}

    def company(instructions, data):
        seen.update(data)
        return stored.company()

    scenario, _, _ = make({"company": company})
    scenario.create_company("IS3328")
    assert seen["module"] == "IS3328"
    assert seen["passages"] and all("id" in p for p in seen["passages"])


def test_an_event_on_an_unknown_task_is_replaced_by_a_stored_event(harbour):
    scenario, engine, _ = make({"event": delay_on("Q", 1)})
    engine.load_company("s1", harbour)
    event = scenario.next_event("s1", "IS3328")
    assert event["source"] == "stored"
    assert engine.check_event("s1", event) == []


def test_an_event_over_the_size_cap_is_rejected(harbour):
    scenario, engine, _ = make({"event": delay_on("B", 5)})
    engine.load_company("s1", harbour)
    assert scenario.next_event("s1", "IS3328")["source"] == "stored"


def test_the_event_prompt_carries_the_cap_and_the_float(harbour):
    seen = {}

    def event(instructions, data):
        seen.update(data)
        return delay_on("B", 2)

    scenario, engine, _ = make({"event": event})
    engine.load_company("s1", harbour)
    assert scenario.next_event("s1", "IS3328")["source"] == "ai"
    assert seen["max_delay"] == 2
    assert {t["id"]: t["float"] for t in seen["tasks"]}["C"] == 2


def test_the_stored_event_passes_the_rules_for_another_company():
    # QuickBrew in weeks, a different shape from Harbour Coffee.
    company = stored.company()
    company["tasks"] = [
        {"id": "A", "name": "Workshops", "duration": 2, "cost": 1000, "after": []},
        {"id": "B", "name": "Sign-off", "duration": 4, "cost": 1000, "after": ["A"]},
        {"id": "C", "name": "Build", "duration": 3, "cost": 1000, "after": ["A"]},
        {"id": "D", "name": "Launch", "duration": 1, "cost": 1000, "after": ["B", "C"]},
    ]
    engine = SimulationEngine()
    engine.load_company("s1", company)
    event = stored.event_for(engine.get_company("s1"))
    assert engine.check_event("s1", event) == []
