"""Stored fallbacks, used when the AI is down or keeps breaking the rules.

The stored company is Harbour Coffee Co. from the Part 1 wireframes. The
stored event is built by code from whatever company the student has, so it
always names real tasks and always passes the engine's rules.
"""

import copy

from ..simulation import event_cap

STORED_COMPANY = {
    "name": "Harbour Coffee Co.",
    "brief": ("A small chain of four Cork cafes. Queues at peak times lose sales, "
              "so the owners want customers to order and pay on their phones."),
    "project": "Mobile ordering and new tills in all four cafes",
    "budget": 60000,
    "team": [
        {"name": "Aoife", "role": "Project manager (you)"},
        {"name": "Tomas", "role": "App developer"},
        {"name": "Niamh", "role": "Cafe operations lead"},
        {"name": "Supplier", "role": "Till and tablet supplier"},
    ],
    "business_case": {
        "summary": ("Mobile ordering should cut peak queues and win back lost sales. "
                    "Every week the launch slips costs about EUR 4,000 in lost sales."),
        "cost_of_delay_per_week": 4000,
    },
    "tasks": [
        {"id": "A", "name": "Agree requirements with cafe managers", "duration": 1, "cost": 2000, "after": []},
        {"id": "B", "name": "Order tills and tablets from supplier", "duration": 3, "cost": 18000, "after": ["A"]},
        {"id": "C", "name": "Build the ordering app", "duration": 4, "cost": 16000, "after": ["A"]},
        {"id": "D", "name": "Install hardware in the cafes", "duration": 3, "cost": 9000, "after": ["B"]},
        {"id": "E", "name": "Connect the app to the tills", "duration": 1, "cost": 4000, "after": ["C", "D"]},
        {"id": "F", "name": "Train cafe staff", "duration": 1, "cost": 3000, "after": ["D"]},
        {"id": "G", "name": "Go live", "duration": 1, "cost": 2000, "after": ["E", "F"]},
    ],
}


def company() -> dict:
    return copy.deepcopy(STORED_COMPANY)


def max_delay(project_length: int) -> int:
    return event_cap(project_length)


def event_for(view) -> dict:
    """A plain delay on the longest critical task, with rule-based responses.

    view is the engine's CompanyView. The target is the longest critical
    task. Crashing works on the longest critical task after it (or the
    target itself), so the response figures always pass the rules.
    """
    critical = [t for t in view.tasks if t["critical"]]
    target = max(critical, key=lambda t: (t["duration"], -t["es"]))
    delay = max_delay(view.length)
    later = [t for t in critical if t["es"] >= target["ef"] and t["duration"] >= 2]
    # Both choices leave room to save one week: a later task is at least two
    # weeks long, and the target is at least two weeks once the delay is added.
    crash_task = max(later, key=lambda t: t["duration"]) if later else target
    saved = 1
    weekly = view.cost_of_delay_per_week
    off_path = next((t for t in view.tasks if not t["critical"] and t["duration"] >= 2), None)

    def response(rid, task, cost, time_saved, note):
        return {"id": rid, "task_id": task["id"], "cost": cost,
                "time_saved": time_saved, "note": note}

    responses = [
        response("crash", crash_task, max(1, round(weekly * 0.75)), saved,
                 f"Pay for overtime on '{crash_task['name']}'."),
        response("fast_track", crash_task, max(1, round(weekly * 0.5)), saved,
                 f"Overlap '{crash_task['name']}' with the next task. Risk of rework."),
        response("re_sequence", off_path or target, 0, 1 if off_path else 0,
                 "Change the order of the work on another path."),
        response("reduce_scope", crash_task, weekly, saved,
                 "Deliver less at first. The lost benefit counts as the cost."),
        response("escalate", target, 0, 0, "Raise an issue with the board and ask it to decide."),
        response("accept", target, 0, 0, "Accept the delay and move the end date."),
    ]
    return {
        "title": f"'{target['name']}' is running {delay} week{'s' if delay > 1 else ''} late",
        "description": ("The AI is unavailable, so this is a stored practice event. "
                        f"'{target['name']}' will take {delay} more week{'s' if delay > 1 else ''} than planned."),
        "task_id": target["id"],
        "delay": delay,
        "responses": responses,
    }
