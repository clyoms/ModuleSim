import pytest

from modulesim.web import create_app

from conftest import FailingClient

REASONING = "Installation is on the critical path, so I crash it with overtime."


@pytest.fixture
def client(config, make_system):
    return create_app(config, make_system()).test_client()


def test_one_month_end_to_end(client):
    assert b"IS3328" in client.get("/").data
    assert client.post("/start", data={"module": "IS3328"}).location.endswith("/dashboard")
    page = client.get("/dashboard").data
    assert b"Harbour Coffee Co." in page and b"Week 9" in page
    client.post("/month/start")
    page = client.get("/month").data
    assert b"two weeks late" in page and b"week 11" in page
    assert b"Do not type personal details" in page          # Risk 3 notice
    client.post("/month/decide", data={"response_id": "crash", "reasoning": REASONING})
    page = client.get("/result").data
    assert b"Week 10" in page
    assert b"AI-written, practice only" in page              # Risk 6 label
    assert b"From your notes:" in page                       # Risk 4 sources shown


def test_only_the_live_module_can_start(client):
    client.post("/start", data={"module": "IS3329"})
    assert b"Only IS3328 is live" in client.get("/").data


def test_a_decision_needs_reasoning(client):
    client.post("/start", data={"module": "IS3328"})
    client.post("/month/start")
    client.post("/month/decide", data={"response_id": "crash", "reasoning": "  "})
    assert b"say why you chose it" in client.get("/month").data


def test_pages_without_a_company_send_you_to_the_picker(client):
    assert client.get("/dashboard").location.endswith("/")
    assert client.get("/month").location.endswith("/")
    assert client.get("/result").location.endswith("/")


def test_ai_outage_shows_a_plain_message_and_no_crash(config, make_system):
    client = create_app(config, make_system([FailingClient()])).test_client()
    client.post("/start", data={"module": "IS3328"})
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert b"stored practice scenario" in page.data
    client.post("/month/start")
    client.post("/month/decide", data={"response_id": "accept", "reasoning": "Accept it."})
    assert b"Not marked: the AI is unavailable" in client.get("/result").data
