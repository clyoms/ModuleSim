"""Shared test helpers. Every test uses a fake AI, so tests are free and repeatable."""

import copy
import time

import pytest

from modulesim.config import Config
from modulesim.llm import LLMError
from modulesim.llm.mock import HARBOUR_COFFEE, SUPPLIER_DELAY_EVENT, MockClient
from modulesim.wiring import build_system


class FailingClient:
    """A provider that always fails, like an outage."""
    name = "failing"

    def __init__(self):
        self.calls = 0

    def complete(self, task, instructions, data, schema, timeout):
        self.calls += 1
        raise LLMError("provider is down")


class SlowClient:
    """A provider that takes longer than the gateway's time limit."""
    name = "slow"

    def __init__(self, seconds=2.0):
        self.seconds = seconds

    def complete(self, task, instructions, data, schema, timeout):
        time.sleep(self.seconds)
        return {}


class RecordingClient(MockClient):
    """The mock, but it remembers what data it was sent."""

    def __init__(self, script=None):
        super().__init__(script)
        self.seen = []

    def complete(self, task, instructions, data, schema, timeout):
        self.seen.append((task, copy.deepcopy(data)))
        return super().complete(task, instructions, data, schema, timeout)


@pytest.fixture
def config():
    return Config(database=":memory:", ai_timeout=0.5)


@pytest.fixture
def make_system(config):
    def _make(providers=None):
        return build_system(config, providers=providers if providers is not None else [MockClient()])
    return _make


@pytest.fixture
def harbour():
    return copy.deepcopy(HARBOUR_COFFEE)


@pytest.fixture
def supplier_event():
    return copy.deepcopy(SUPPLIER_DELAY_EVENT)


def delay_on(task_id, weeks, responses=None):
    """An event that delays one task, with valid responses for Harbour Coffee."""
    event = copy.deepcopy(SUPPLIER_DELAY_EVENT)
    event.update(title=f"Task {task_id} slips", task_id=task_id, delay=weeks)
    if responses:
        event["responses"] = responses
    return event
