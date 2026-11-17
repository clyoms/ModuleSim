from modulesim.identity import DEMO_STUDENT, DemoIdentity
from modulesim.progress import ProgressStore


def attempt(student="s1", band="2.1 (60-69)", response="crash"):
    return {
        "student_id": student, "module": "IS3328", "reasoning": "Because of the critical path.",
        "topics": ["Critical path"],
        "result": {"event_title": "Supplier late", "response_id": response, "end_after_decision": 10},
        "feedback": {"band": band, "flagged": False, "good_points": []},
    }


def test_a_saved_attempt_reads_back_with_its_topics_and_result(tmp_path):
    store = ProgressStore(str(tmp_path / "test.db"))
    store.save_attempt(attempt())
    saved = store.latest("s1")
    assert saved["topics"] == ["Critical path"]
    assert saved["result"]["end_after_decision"] == 10
    assert saved["band"] == "2.1 (60-69)"
    assert saved["flagged"] is False


def test_attempts_come_back_newest_first_and_per_student():
    store = ProgressStore(":memory:")
    store.save_attempt(attempt(response="accept"))
    store.save_attempt(attempt(response="crash"))
    store.save_attempt(attempt(student="s2"))
    assert [a["response_id"] for a in store.attempts("s1")] == ["crash", "accept"]
    assert len(store.attempts("s2")) == 1
    assert store.latest("nobody") is None


def test_the_data_survives_a_restart(tmp_path):
    path = str(tmp_path / "test.db")
    ProgressStore(path).save_attempt(attempt())
    assert ProgressStore(path).latest("s1") is not None


def test_identity_always_returns_the_demo_student():
    assert DemoIdentity().current_student() == DEMO_STUDENT
