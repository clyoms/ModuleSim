import pytest

from modulesim.events import EventBus, messages as m


def test_subscriber_gets_only_its_messages_in_order():
    bus = EventBus()
    seen = []
    bus.subscribe(m.MONTH_STARTED, lambda msg: seen.append(("month", msg["n"])))
    bus.subscribe(m.FEEDBACK_READY, lambda msg: seen.append(("feedback", msg["n"])))

    bus.publish(m.MONTH_STARTED, {"n": 1})
    bus.publish(m.RESULT_READY, {"n": 2})   # nobody listens to this one
    bus.publish(m.MONTH_STARTED, {"n": 3})
    bus.publish(m.FEEDBACK_READY, {"n": 4})

    assert seen == [("month", 1), ("month", 3), ("feedback", 4)]


def test_handlers_run_in_the_order_they_subscribed():
    bus = EventBus()
    order = []
    bus.subscribe(m.EVENT_READY, lambda msg: order.append("first"))
    bus.subscribe(m.EVENT_READY, lambda msg: order.append("second"))
    bus.publish(m.EVENT_READY)
    assert order == ["first", "second"]


def test_unknown_message_names_are_rejected():
    bus = EventBus()
    with pytest.raises(ValueError):
        bus.subscribe("month begun", lambda msg: None)
    with pytest.raises(ValueError):
        bus.publish("month begun", {})


def test_history_records_every_message():
    bus = EventBus()
    bus.publish(m.MONTH_STARTED, {"student_id": "s1"})
    assert bus.history == [(m.MONTH_STARTED, {"student_id": "s1"})]
