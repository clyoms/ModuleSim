import pytest

from modulesim.llm import AIGateway, AIUnavailable
from modulesim.llm.checks import redact, shape_problems
from modulesim.llm.mock import MockClient

from conftest import FailingClient, RecordingClient, SlowClient

SCHEMA = {"type": "object", "required": ["answer"], "properties": {"answer": {"type": "integer"}}}


def test_first_provider_answer_is_returned():
    gateway = AIGateway([MockClient({"sum": {"answer": 4}})])
    assert gateway.complete("sum", "add", {}, SCHEMA) == {"answer": 4}


def test_failing_provider_is_retried_once_then_next_provider_is_used():
    failing = FailingClient()
    gateway = AIGateway([failing, MockClient({"sum": {"answer": 4}})], retries=1)
    assert gateway.complete("sum", "add", {}, SCHEMA) == {"answer": 4}
    assert failing.calls == 2   # the first try plus one retry
    assert [c.provider for c in gateway.calls] == ["failing", "failing", "mock"]


def test_timeout_passes_the_request_to_the_next_provider():
    gateway = AIGateway([SlowClient(seconds=2), MockClient({"sum": {"answer": 4}})],
                        timeout=0.2, retries=0)
    assert gateway.complete("sum", "add", {}, SCHEMA) == {"answer": 4}
    assert "timed out" in gateway.calls[0].detail


def test_all_providers_failing_raises_ai_unavailable():
    gateway = AIGateway([FailingClient(), FailingClient()])
    with pytest.raises(AIUnavailable):
        gateway.complete("sum", "add", {}, SCHEMA)


def test_answer_with_the_wrong_shape_counts_as_a_failure():
    gateway = AIGateway([MockClient({"sum": {"answer": "four"}})], retries=1)
    with pytest.raises(AIUnavailable):
        gateway.complete("sum", "add", {}, SCHEMA)
    assert len(gateway.calls) == 2
    assert "should be integer" in gateway.calls[0].detail


def test_emails_and_student_numbers_never_reach_the_provider():
    recorder = RecordingClient({"sum": {"answer": 1}})
    AIGateway([recorder]).complete(
        "sum", "add", {"reasoning": "I am 124357031, mail me at jo@umail.ucc.ie"}, SCHEMA)
    sent = recorder.seen[0][1]["reasoning"]
    assert "124357031" not in sent and "jo@umail.ucc.ie" not in sent
    assert "[number removed]" in sent and "[email removed]" in sent


def test_redact_leaves_normal_numbers_alone():
    assert redact("The delay is 2 weeks and costs EUR 4000") == "The delay is 2 weeks and costs EUR 4000"


def test_shape_check_catches_enum_and_nested_problems():
    schema = {"type": "object", "required": ["band", "points"], "properties": {
        "band": {"type": "string", "enum": ["First", "Fail"]},
        "points": {"type": "array", "items": {"type": "object", "required": ["quote"]}}}}
    problems = shape_problems({"band": "Top", "points": [{}]}, schema)
    assert any("must be one of" in p for p in problems)
    assert any("points[0].quote is missing" in p for p in problems)


def test_true_is_not_accepted_as_a_number():
    assert shape_problems(True, {"type": "integer"})
