"""The rules every AI number must pass before it is used (Part 1, Risks 5 and 8).

The AI writes the story and suggests figures. These checks decide whether
the figures are allowed. Each function returns a list of problems in plain
words. An empty list means the data passed.
"""

from .cpm import critical_path

RESPONSE_IDS = ["crash", "fast_track", "re_sequence", "reduce_scope", "escalate", "accept"]
MAX_TASK_LENGTH = 52   # weeks
EVENT_CAP_SHARE = 0.25  # an event may delay the project by at most 25% of its length


def _is_whole_number(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def company_problems(company: dict) -> list[str]:
    problems: list[str] = []
    tasks = company.get("tasks", [])
    if not company.get("name"):
        problems.append("The company has no name")
    if len(tasks) < 2:
        problems.append("The project needs at least two tasks")
        return problems

    ids = [t.get("id") for t in tasks]
    if len(set(ids)) != len(ids):
        problems.append("Two tasks share the same id")
    for t in tasks:
        d, c = t.get("duration"), t.get("cost")
        if not _is_whole_number(d) or not 1 <= d <= MAX_TASK_LENGTH:
            problems.append(f"Task {t.get('id')} has an impossible length: {d!r}")
        if not _is_whole_number(c) or c < 0:
            problems.append(f"Task {t.get('id')} has an impossible cost: {c!r}")
    if problems:
        return problems

    try:
        critical_path({t["id"]: t["duration"] for t in tasks},
                      {t["id"]: t.get("after", []) for t in tasks})
    except ValueError as error:
        problems.append(str(error))

    budget = company.get("budget")
    total = sum(t["cost"] for t in tasks)
    if not _is_whole_number(budget) or budget < total:
        problems.append(f"The budget ({budget!r}) does not cover the plan ({total})")
    delay_cost = company.get("business_case", {}).get("cost_of_delay_per_week")
    if not _is_whole_number(delay_cost) or delay_cost < 0:
        problems.append(f"The cost of delay per week is impossible: {delay_cost!r}")
    return problems


def event_cap(project_length: int) -> int:
    """The largest delay an event may cause. Always at least one week."""
    return max(1, int(project_length * EVENT_CAP_SHARE))


def event_problems(tasks: dict[str, dict], project_length: int, event: dict) -> list[str]:
    """tasks: task id -> task dict (the company's current tasks)."""
    problems: list[str] = []
    target, delay = event.get("task_id"), event.get("delay")
    if target not in tasks:
        problems.append(f"The event names an unknown task: {target!r}")
    if not _is_whole_number(delay) or delay < 1:
        problems.append(f"The event delay is impossible: {delay!r}")
    elif delay > event_cap(project_length):
        problems.append(
            f"The event delay ({delay}) is over the cap of {event_cap(project_length)} "
            f"(25% of a {project_length}-week project)"
        )

    responses = event.get("responses", [])
    if sorted(r.get("id") for r in responses) != sorted(RESPONSE_IDS):
        problems.append(f"The event must offer each response once: {RESPONSE_IDS}")
    for r in responses:
        problems += response_problems(tasks, event, r)
    return problems


def response_problems(tasks: dict[str, dict], event: dict, response: dict) -> list[str]:
    rid, task_id = response.get("id"), response.get("task_id")
    cost, saved = response.get("cost"), response.get("time_saved")
    problems: list[str] = []
    if task_id not in tasks:
        return [f"Response {rid} names an unknown task: {task_id!r}"]
    if not _is_whole_number(cost) or cost < 0:
        problems.append(f"Response {rid} has an impossible cost: {cost!r}")
    if not _is_whole_number(saved) or saved < 0:
        problems.append(f"Response {rid} has an impossible time saving: {saved!r}")
    if problems:
        return problems

    length = tasks[task_id]["duration"]
    if task_id == event.get("task_id"):
        length += event.get("delay", 0)
    if saved > length - 1:
        problems.append(f"Response {rid} would shrink task {task_id} below one week")
    if rid == "crash" and not (cost > 0 and saved > 0):
        problems.append("Crashing must cost more and finish sooner")
    if rid in ("accept", "escalate") and saved != 0:
        problems.append(f"Response {rid} cannot save time on its own")
    if rid == "accept" and cost != 0:
        problems.append("Accepting the delay has no direct cost")
    return problems
