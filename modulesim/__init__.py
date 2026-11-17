"""ModuleSim: an AI module simulator (IS3329 prototype).

One Flask application, one Python package per component in the Part 1
design. Each package is reached only through its interface:

    events      Event bus: in-app message passer (Simplified)
    llm         AI gateway: the one route to any AI model (Built)
    simulation  Simulation engine: checks numbers, critical path, budget (Built)
    content     Course content: IS3328 notes and keyword search (Simplified)
    scenario    Scenario: creates the company and each month's event (Built)
    feedback    Feedback marker: marks reasoning, checks citations (Built)
    progress    Progress: saves attempts in one SQLite table (Simplified)
    identity    Identity: one fixed demo student (Mocked)
    web         Student web app and API gateway: Flask pages (Simplified)

wiring.py connects them. It is the only file that knows about all of them.
"""
