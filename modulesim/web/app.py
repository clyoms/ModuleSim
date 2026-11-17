"""Student web app and API gateway (Simplified): Flask pages and routes.

Routes only pass requests on and show results. They hold no sums and make
no AI calls: they publish a message on the event bus, then read the answer
back through a component's interface.

    GET  /               Wireframe 1: module picker
    POST /start          ask for a company
    GET  /dashboard      Wireframe 2: company dashboard
    POST /month/start    start a month
    GET  /month          Wireframe 3: month event and decision
    POST /month/decide   submit a response and the reasoning
    GET  /result         Wireframe 4: result and feedback
"""

from flask import Flask, flash, redirect, render_template, request, session, url_for

from ..config import Config
from ..events import messages as m
from ..simulation import RejectedData
from ..wiring import System, build_system

LIVE_MODULES = {"IS3328": "Project Management for Information Systems"}
COMING_LATER = {"IS3322": "Business Analytics", "IS3329": "Application Architectures"}
RESPONSE_LABELS = {
    "crash": "Crash the schedule (overtime)",
    "fast_track": "Fast-track (overlap tasks)",
    "re_sequence": "Re-sequence tasks",
    "reduce_scope": "Reduce scope",
    "escalate": "Escalate to the sponsor",
    "accept": "Accept the delay",
}
MAX_REASONING = 2000


def create_app(config: Config | None = None, system: System | None = None) -> Flask:
    config = config or Config.from_environment()
    system = system or build_system(config)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    app.extensions["modulesim"] = system

    def student_id() -> str:
        return system.identity.current_student().id

    def notice() -> None:
        message = system.notices.pop(student_id(), None)
        if message:
            flash(message, "notice")

    @app.get("/")
    def picker():
        return render_template("picker.html", live=LIVE_MODULES, later=COMING_LATER,
                               student=system.identity.current_student())

    @app.post("/start")
    def start():
        module = request.form.get("module", "")
        if module not in LIVE_MODULES:
            flash("Only IS3328 is live in this prototype.", "error")
            return redirect(url_for("picker"))
        session["module"] = module
        system.bus.publish(m.COMPANY_REQUESTED, {"student_id": student_id(), "module": module})
        return redirect(url_for("dashboard"))

    @app.get("/dashboard")
    def dashboard():
        if not system.engine.has_company(student_id()):
            return redirect(url_for("picker"))
        notice()
        return render_template("dashboard.html", company=system.engine.get_company(student_id()),
                               module=session.get("module"))

    @app.post("/month/start")
    def month_start():
        if not system.engine.has_company(student_id()):
            return redirect(url_for("picker"))
        system.bus.publish(m.MONTH_STARTED, {"student_id": student_id(),
                                             "module": session.get("module", "IS3328")})
        return redirect(url_for("month"))

    @app.get("/month")
    def month():
        if not system.engine.has_company(student_id()):
            return redirect(url_for("picker"))
        event = system.engine.current_event(student_id())
        if event is None:
            return redirect(url_for("dashboard"))
        notice()
        return render_template("month.html", event=event, labels=RESPONSE_LABELS,
                               company=system.engine.get_company(student_id()),
                               max_reasoning=MAX_REASONING)

    @app.post("/month/decide")
    def decide():
        response_id = request.form.get("response_id", "")
        reasoning = request.form.get("reasoning", "").strip()
        if response_id not in RESPONSE_LABELS or not reasoning:
            flash("Pick a response and say why you chose it.", "error")
            return redirect(url_for("month"))
        try:
            system.bus.publish(m.DECISION_SUBMITTED, {
                "student_id": student_id(), "module": session.get("module", "IS3328"),
                "response_id": response_id, "reasoning": reasoning[:MAX_REASONING],
            })
        except RejectedData as error:
            flash(f"That decision could not be applied: {error}", "error")
            return redirect(url_for("dashboard"))
        return redirect(url_for("result"))

    @app.get("/result")
    def result():
        attempt = system.progress.latest(student_id())
        if attempt is None:
            return redirect(url_for("picker"))
        return render_template("result.html", attempt=attempt, labels=RESPONSE_LABELS,
                               company=system.engine.get_company(student_id()))

    return app
