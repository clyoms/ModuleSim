import pytest

from modulesim.simulation import RejectedData, SimulationEngine

from conftest import delay_on


@pytest.fixture
def engine(harbour):
    e = SimulationEngine()
    e.load_company("s1", harbour)
    return e


def test_harbour_coffee_plan_ends_in_week_9(engine):
    view = engine.get_company("s1")
    assert view.length == 9
    assert view.critical_paths == [["A", "B", "D", "E", "G"], ["A", "B", "D", "F", "G"]]
    assert {t["id"]: t["float"] for t in view.tasks}["C"] == 2


def test_delay_on_a_critical_task_moves_the_end_date(engine, supplier_event):
    assert engine.apply_event("s1", supplier_event).length == 11


def test_delay_within_float_leaves_the_end_date_alone(engine):
    assert engine.apply_event("s1", delay_on("C", 2)).length == 9


def test_crashing_shortens_the_schedule_and_raises_the_cost(engine, supplier_event):
    engine.apply_event("s1", supplier_event)
    result = engine.apply_decision("s1", "crash")
    assert (result["end_after_event"], result["end_after_decision"]) == (11, 10)
    assert result["response_cost"] == 3000
    assert result["delay_cost"] == 4000           # one week late at EUR 4,000
    assert result["total_cost"] == 54000 + 3000 + 4000


def test_ai_figures_are_applied_exactly(engine, supplier_event):
    engine.apply_event("s1", supplier_event)
    engine.apply_decision("s1", "crash")
    tasks = {t["id"]: t for t in engine.get_company("s1").tasks}
    assert tasks["B"]["duration"] == 5   # 3 + the 2-week delay
    assert tasks["D"]["duration"] == 2   # 3 - the 1 week saved


def test_accepting_a_critical_delay_slips_the_end_date(engine, supplier_event):
    engine.apply_event("s1", supplier_event)
    result = engine.apply_decision("s1", "accept")
    assert result["end_after_decision"] == 11
    assert result["weeks_late"] == 2
    assert result["delay_cost"] == 8000


def test_a_decision_needs_an_event_first(engine):
    with pytest.raises(RejectedData):
        engine.apply_decision("s1", "crash")


@pytest.mark.parametrize("change, message", [
    (lambda c: c["tasks"][0].update(duration=-2), "impossible length"),
    (lambda c: c["tasks"][1].update(cost=-5), "impossible cost"),
    (lambda c: c.update(budget=1000), "does not cover the plan"),
    (lambda c: c["tasks"][2].update(after=["Z"]), "unknown task"),
    (lambda c: c["tasks"][0].update(after=["G"]), "loop"),
])
def test_impossible_companies_are_rejected(harbour, change, message):
    change(harbour)
    with pytest.raises(RejectedData, match=message):
        SimulationEngine().load_company("s1", harbour)


def test_event_over_the_25_percent_cap_is_rejected(engine):
    # 25% of a 9-week project is 2 weeks.
    with pytest.raises(RejectedData, match="over the cap"):
        engine.apply_event("s1", delay_on("B", 3))


def test_event_on_an_unknown_task_is_rejected(engine):
    with pytest.raises(RejectedData, match="unknown task"):
        engine.apply_event("s1", delay_on("Q", 1))


@pytest.mark.parametrize("bad, message", [
    ({"id": "crash", "task_id": "D", "cost": 0, "time_saved": 1}, "must cost more"),
    ({"id": "crash", "task_id": "D", "cost": 500, "time_saved": 5}, "below one week"),
    ({"id": "accept", "task_id": "B", "cost": 900, "time_saved": 0}, "no direct cost"),
    ({"id": "escalate", "task_id": "B", "cost": 0, "time_saved": 1}, "cannot save time"),
    ({"id": "fast_track", "task_id": "D", "cost": -1, "time_saved": 1}, "impossible cost"),
])
def test_response_figures_that_break_the_rules_are_rejected(engine, supplier_event, bad, message):
    supplier_event["responses"] = [
        {**r, **bad, "note": ""} if r["id"] == bad["id"] else r for r in supplier_event["responses"]
    ]
    with pytest.raises(RejectedData, match=message):
        engine.apply_event("s1", supplier_event)


def test_every_response_must_be_offered_once(engine, supplier_event):
    supplier_event["responses"] = supplier_event["responses"][:5]
    with pytest.raises(RejectedData, match="each response once"):
        engine.apply_event("s1", supplier_event)
