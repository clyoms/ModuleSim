# ModuleSim

An AI module simulator, built for IS3329 Application Architectures and Emerging Technologies (Deliverable 2: Component Implementation).

Each student gets a fictional company and one simulated month of IS3328 Project Management. An AI writes the company, the month's problem and the feedback. Normal code checks the AI's numbers and does every sum, so the story can change but the maths stays right.

The app runs on a **mock AI** by default. It needs no key, no internet and no money. A real Google Gemini model can be switched on with a free key.

## What you need

- Python 3.12 or newer (`python --version` to check)
- About 50 MB of disk space

## Install

From this folder, in a terminal:

```bash
python -m venv .venv
```

Then switch the terminal to that environment.

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (Command Prompt): `.venv\Scripts\activate.bat`
- macOS or Linux: `source .venv/bin/activate`

Then install the two libraries:

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m modulesim
```

Open <http://127.0.0.1:5000> in a browser. Pick IS3328, read the company dashboard, start month 1, choose a response, explain why, and read the feedback. Press `Ctrl+C` in the terminal to stop.

## Test

```bash
python -m pytest
```

All tests use the mock AI, so they pass with no key and no internet.

## Use the real Gemini model (optional)

1. Get a free API key at <https://aistudio.google.com>.
2. Copy `.env.example` to a new file called `.env`.
3. In `.env`, set `AI_PROVIDER=gemini` and paste your key after `GEMINI_API_KEY=`.
4. Check the key works: `python scripts/check_gemini.py`
5. Run the app as above.

`.env` is listed in `.gitignore`, so the key never reaches the repository. The key is only read on the server. It is never sent to the browser or written to a log.

Before you submit or push, scan for keys: `python scripts/check_secrets.py` checks the folder, and `python scripts/check_secrets.py ModuleSim.zip` checks a finished zip.

If Gemini is slow or down, the app waits 20 seconds, tries once more, then switches to a stored practice scenario and says so on screen.

## How the code maps to the design

One Python package per component in the Part 1 architecture. Components talk only through each other's interfaces, and `wiring.py` connects them through the event bus.

| Part 1 component | Package | Label | Interface |
|---|---|---|---|
| Student web app and API gateway | `modulesim/web` | Simplified | Flask routes |
| Identity | `modulesim/identity` | Mocked | `current_student()` |
| Course content and notes store | `modulesim/content` | Simplified | `search()`, `get()`, `quote_matches()` |
| Scenario | `modulesim/scenario` | Built | `create_company()`, `next_event()` |
| Simulation engine | `modulesim/simulation` | Built | `check_company()`, `check_event()`, `load_company()`, `apply_event()`, `apply_decision()`, `get_company()` |
| Feedback marker | `modulesim/feedback` | Built | `mark()` |
| Progress and analytics | `modulesim/progress` | Simplified | `save_attempt()`, `latest()`, `attempts()` |
| Event bus | `modulesim/events` | Simplified | `publish()`, `subscribe()` |
| AI gateway and providers | `modulesim/llm` | Built | `AIGateway.complete()` |
| Database | `instance/modulesim.db` (SQLite, made on first run) | Simplified | through `progress` |
| Lecturer portal | not present | Deferred | see the technical document |
| UCC sign-in | not present | Deferred | see the technical document |

## Folder layout

```text
modulesim/
  __main__.py      starts the web app
  config.py        reads settings from the environment or .env
  wiring.py        builds every component and connects them through the event bus
  events/          event bus and message names
  llm/             AI gateway, mock AI and Gemini client
  simulation/      critical path, number rules and the engine
  content/         IS3328 notes and keyword search
  scenario/        company and event creation, stored fallbacks
  feedback/        marking, citation check, injection flag
  progress/        attempts in SQLite
  identity/        the demo student
  web/             Flask routes, templates and styles
scripts/check_gemini.py   one real Gemini call to test a key
tests/                    pytest tests, one file per component plus the six Part 1 scenario runs
```

## Data

All data is synthetic. The companies are made up. The course notes in `modulesim/content/notes/is3328/` are written from my own IS3328 study notes, not from the lecturer's slides. `responses-to-delay.txt` was written for the prototype to cover crashing, fast-tracking and re-sequencing.
