"""Critical path method, the IS3328 forward and backward pass.

    Early start (ES):  first task 0, otherwise the LARGEST EF of its predecessors
    Early finish (EF): ES + duration
    Late finish (LF):  last task = project length, otherwise the SMALLEST LS of its successors
    Late start (LS):   LF - duration
    Float:             LS - ES. Zero float means the task is critical.

The rules above are copied from my IS3328 critical path note.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Schedule:
    length: int
    es: dict[str, int]
    ef: dict[str, int]
    ls: dict[str, int]
    lf: dict[str, int]
    float: dict[str, int]
    critical_tasks: list[str]   # tasks with zero float, in start order
    critical_paths: list[list[str]]  # every chain of critical tasks, start to end


def _topological_order(durations: dict[str, int], after: dict[str, list[str]]) -> list[str]:
    """Order tasks so every task comes after its predecessors. Rejects loops."""
    for task, preds in after.items():
        for p in preds:
            if p not in durations:
                raise ValueError(f"Task {task} depends on unknown task {p}")
    order, done, visiting = [], set(), set()

    def visit(task: str) -> None:
        if task in done:
            return
        if task in visiting:
            raise ValueError(f"Tasks form a loop at {task}")
        visiting.add(task)
        for p in after.get(task, []):
            visit(p)
        visiting.discard(task)
        done.add(task)
        order.append(task)

    for task in durations:  # keeps the input order where it can
        visit(task)
    return order


def critical_path(durations: dict[str, int], after: dict[str, list[str]]) -> Schedule:
    """durations: task id -> length. after: task id -> list of predecessor ids."""
    if not durations:
        raise ValueError("A schedule needs at least one task")
    order = _topological_order(durations, after)
    successors: dict[str, list[str]] = {t: [] for t in durations}
    for task in order:
        for p in after.get(task, []):
            successors[p].append(task)

    # Forward pass (left to right).
    es, ef = {}, {}
    for task in order:
        preds = after.get(task, [])
        es[task] = max((ef[p] for p in preds), default=0)
        ef[task] = es[task] + durations[task]
    length = max(ef.values())

    # Backward pass (right to left).
    ls, lf = {}, {}
    for task in reversed(order):
        succs = successors[task]
        lf[task] = min((ls[s] for s in succs), default=length)
        ls[task] = lf[task] - durations[task]

    slack = {t: ls[t] - es[t] for t in order}
    critical = sorted((t for t in order if slack[t] == 0), key=lambda t: (es[t], order.index(t)))

    # Follow critical links: a critical task feeds a critical successor
    # with no gap between them.
    def chains_from(task: str) -> list[list[str]]:
        nexts = [s for s in successors[task] if slack[s] == 0 and es[s] == ef[task]]
        if not nexts:
            return [[task]]
        return [[task] + rest for s in nexts for rest in chains_from(s)]

    starts = [t for t in critical if es[t] == 0]
    paths = [p for s in starts for p in chains_from(s) if ef[p[-1]] == length]
    return Schedule(length, es, ef, ls, lf, slack, critical, paths)
