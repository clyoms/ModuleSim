"""The answer shapes Scenario asks the AI for (JSON Schema subset)."""

from ..simulation import RESPONSE_IDS

TASK = {
    "type": "object",
    "required": ["id", "name", "duration", "cost", "after"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "duration": {"type": "integer"},
        "cost": {"type": "integer"},
        "after": {"type": "array", "items": {"type": "string"}},
    },
}

COMPANY = {
    "type": "object",
    "required": ["name", "brief", "project", "budget", "team", "business_case", "tasks"],
    "properties": {
        "name": {"type": "string"},
        "brief": {"type": "string"},
        "project": {"type": "string"},
        "budget": {"type": "integer"},
        "team": {
            "type": "array",
            "items": {"type": "object", "required": ["name", "role"],
                      "properties": {"name": {"type": "string"}, "role": {"type": "string"}}},
        },
        "business_case": {
            "type": "object",
            "required": ["summary", "cost_of_delay_per_week"],
            "properties": {"summary": {"type": "string"},
                           "cost_of_delay_per_week": {"type": "integer"}},
        },
        "tasks": {"type": "array", "items": TASK},
    },
}

RESPONSE = {
    "type": "object",
    "required": ["id", "task_id", "cost", "time_saved", "note"],
    "properties": {
        "id": {"type": "string", "enum": RESPONSE_IDS},
        "task_id": {"type": "string"},
        "cost": {"type": "integer"},
        "time_saved": {"type": "integer"},
        "note": {"type": "string"},
    },
}

EVENT = {
    "type": "object",
    "required": ["title", "description", "task_id", "delay", "responses"],
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "task_id": {"type": "string"},
        "delay": {"type": "integer"},
        "responses": {"type": "array", "items": RESPONSE},
    },
}
