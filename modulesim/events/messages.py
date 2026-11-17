"""The message names, the same ones used in the Part 1 data flow.

Keeping them in one place means a real message queue could later use the
same names without any service changing.
"""

COMPANY_REQUESTED = "company requested"
COMPANY_CREATED = "company created"
MONTH_STARTED = "month started"
EVENT_READY = "event ready"
STATE_UPDATED = "state updated"
DECISION_SUBMITTED = "decision submitted"
RESULT_READY = "result ready"
FEEDBACK_READY = "feedback ready"
ATTEMPT_SAVED = "attempt saved"

ALL = [
    COMPANY_REQUESTED,
    COMPANY_CREATED,
    MONTH_STARTED,
    EVENT_READY,
    STATE_UPDATED,
    DECISION_SUBMITTED,
    RESULT_READY,
    FEEDBACK_READY,
    ATTEMPT_SAVED,
]
