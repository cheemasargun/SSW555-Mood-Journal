from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from datetime import date, datetime, timedelta

# Your domain logic
from mood_mastery.mood_journal import Mood_Journal
from mood_mastery.entry import BIOMETRICS, Entry

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-key"  # or use env var in real life

# In-memory journal instance
mj = Mood_Journal()

# ---------------------------------
# Theme configuration
# ---------------------------------

THEME_CHOICES = {
    "indigo": {
        "label": "Indigo",
        "accent": "79 70 229",       # rgb(79, 70, 229)
        "accent_soft": "165 180 252" # rgb(165, 180, 252)
    },
    "emerald": {
        "label": "Emerald",
        "accent": "16 185 129",      # rgb(16, 185, 129)
        "accent_soft": "167 243 208" # rgb(167, 243, 208)
    },
    "rose": {
        "label": "Rose",
        "accent": "244 63 94",       # rgb(244, 63, 94)
        "accent_soft": "254 202 202" # rgb(254, 202, 202)
    },
    "amber": {
        "label": "Amber",
        "accent": "245 158 11",      # rgb(245, 158, 11)
        "accent_soft": "253 230 138" # rgb(253, 230, 138)
    },
}


@app.context_processor
def inject_theme():
    """Make theme info available to all templates."""
    theme_name = session.get("theme", "indigo")
    if theme_name not in THEME_CHOICES:
        theme_name = "indigo"
    theme = THEME_CHOICES[theme_name]
    return {
        "current_theme_name": theme_name,
        "current_theme": theme,
        "theme_choices": THEME_CHOICES,
    }


@app.post("/theme")
def set_theme():
    """Change the current UI theme and redirect back."""
    theme = request.form.get("theme", "indigo")
    if theme not in THEME_CHOICES:
        theme = "indigo"
    session["theme"] = theme
    # Go back where we came from, or home as fallback
    return redirect(request.referrer or url_for("index"))


# ---------------------------------
# Jinja helpers
# ---------------------------------

def ranking_emoji(r: int) -> str:
    """
    Convenience wrapper so templates can call ranking_emoji(r).
    Uses Entry.determine_ranking_emoji internally.
    """
    tmp = Entry("tmp", 1, 1, 2000, "", r, 50)
    return tmp.determine_ranking_emoji()


app.jinja_env.globals["ranking_emoji"] = ranking_emoji
app.jinja_env.globals["BIOMETRICS"] = BIOMETRICS

# Simple global password for all private entries (demo only)
ENTRY_PASSWORD: str | None = None


def _streak_summary_for_ui():
    s = mj.get_streak_summary()
    last = s["last_entry_date"]
    return {
        "current": s["current_streak"],
        "longest": s["longest_streak"],
        "last": last.isoformat() if last else None,
    }


def _sorted_entries():
    entries = mj.mj_get_all_entries()
    # newest first
    entries.sort(key=lambda e: (e.entry_date, getattr(e, "entry_id_str", "")), reverse=True)
    return entries


def _build_report_dict(title: str, counts: list[int], start: date, end: date) -> dict:
    total = sum(counts)
    bars = []
    if total > 0:
        for idx, count in enumerate(counts, start=1):
            if count == 0:
                continue
            pct = (count / total) * 100
            bars.append(
                {
                    "rank": idx,
                    "emoji": ranking_emoji(idx),
                    "count": count,
                    "pct": round(pct, 1),
                }
            )
    return {
        "title": title,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total": total,
        "bars": bars,
    }


# =========================================================
# Routes
# =========================================================

@app.route("/")
def index():
    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()
    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
    )


# ---------- CRUD for entries ----------

@app.post("/entries/add")
def add_entry():
    title = request.form.get("title", "").strip()
    year = int(request.form.get("year"))
    month = int(request.form.get("month"))
    day = int(request.form.get("day"))
    body = request.form.get("body", "")
    ranking = int(request.form.get("ranking", "5"))

    # Mood rating (1–100), default 50 if not provided
    mood_rating_raw = request.form.get("mood_rating", "").strip()
    try:
        mood_rating = int(mood_rating_raw)
    except ValueError:
        mood_rating = 50
    mood_rating = max(1, min(100, mood_rating))

    # Tags
    tags_str = request.form.get("tags", "")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

    # Biometrics
    biometrics = {}
    for key in BIOMETRICS.keys():
        val = request.form.get(f"bio_{key}", "").strip()
        if val:
            biometrics[key] = val

    mj.mj_log_entry(
        title,
        day,
        month,
        year,
        body,
        ranking,
        mood_rating,
        tags=tags,
        biometrics=biometrics if biometrics else None,
    )
    flash("Entry created ✅", "success")
    return redirect(url_for("index"))


@app.get("/entries/<entry_id>")
def view_entry(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()

    # By default: if not private, show body; if private, ask password
    view_body = None
    view_ask_password = False
    if not e.is_private_check():
        view_body = e.entry_body
    else:
        view_ask_password = True

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        view_e=e,
        view_body=view_body,
        view_ask_password=view_ask_password,
        open_view_modal=True,
        open_edit_modal=False,
        open_report_modal=False,
    )


@app.post("/entries/<entry_id>/unlock")
def unlock_entry(entry_id):
    global ENTRY_PASSWORD
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    pw = request.form.get("password", "")
    if ENTRY_PASSWORD is None or pw != ENTRY_PASSWORD:
        flash("Incorrect password.", "error")
        return redirect(url_for("view_entry", entry_id=entry_id))

    # Correct password: show the body
    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=True,
        view_e=e,
        view_body=e.entry_body,
        view_ask_password=False,
        open_view_modal=True,
        open_edit_modal=False,
        open_report_modal=False,
    )


@app.get("/entries/<entry_id>/edit")
def edit_entry_open(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        edit_e=e,
        open_edit_modal=True,
        open_view_modal=False,
        open_report_modal=False,
    )


@app.post("/entries/<entry_id>/edit")
def edit_entry_save(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    title = request.form.get("title", "").strip()
    year = int(request.form.get("year"))
    month = int(request.form.get("month"))
    day = int(request.form.get("day"))
    body = request.form.get("body", "")
    ranking = int(request.form.get("ranking", "5"))

    mood_rating_raw = request.form.get("mood_rating", "").strip()
    try:
        mood_rating = int(mood_rating_raw)
    except ValueError:
        mood_rating = e.mood_rating
    mood_rating = max(1, min(100, mood_rating))

    mj.mj_edit_entry(
        entry_id,
        title,
        day,
        month,
        year,
        body,
        ranking,
        mood_rating,
    )
    flash("Entry updated ✅", "success")
    return redirect(url_for("index"))


@app.post("/entries/<entry_id>/delete")
def delete_entry(entry_id):
    if mj.mj_delete_entry(entry_id):
        flash("Entry deleted.", "success")
    else:
        flash("Entry not found.", "error")
    return redirect(url_for("index"))


# ---------- Privacy ----------

@app.post("/entries/<entry_id>/make-private")
def make_private(entry_id):
    global ENTRY_PASSWORD
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    if ENTRY_PASSWORD is None:
        pw = request.form.get("password", "").strip()
        if not pw:
            flash("Password required to make private.", "error")
            return redirect(url_for("view_entry", entry_id=entry_id))
        ENTRY_PASSWORD = pw

    e.set_privacy_setting(True)
    flash("Entry set to private 🔒", "success")
    return redirect(url_for("index"))


# ---------- Tags ----------

@app.post("/entries/<entry_id>/tags/add")
def add_tag(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    tag = request.form.get("tag", "")
    if e.add_tag(tag):
        flash("Tag added.", "success")
    else:
        flash("Tag not added (maybe empty or duplicate).", "error")
    return redirect(url_for("edit_entry_open", entry_id=entry_id))


@app.post("/entries/<entry_id>/tags/delete")
def delete_tag(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    tag = request.form.get("tag", "")
    if e.remove_tag(tag):
        flash("Tag removed.", "success")
    else:
        flash("Tag not found.", "error")
    return redirect(url_for("edit_entry_open", entry_id=entry_id))


@app.post("/entries/<entry_id>/tags/clear")
def clear_tags(entry_id):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    e.clear_tags()
    flash("All tags cleared.", "success")
    return redirect(url_for("edit_entry_open", entry_id=entry_id))


# ---------- Biometrics ----------

@app.post("/entries/<entry_id>/biometric/clear/<key>")
def clear_biometric(entry_id, key):
    e = mj.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    e.delete_biometric(key)
    flash(f"Biometric '{key}' cleared.", "success")
    return redirect(url_for("edit_entry_open", entry_id=entry_id))


# ---------- Reports (weekly / monthly) ----------

@app.get("/report/weekly")
def weekly_report():
    today = date.today()
    counts = mj.mj_weekly_report(today.day, today.month, today.year)
    if counts is None:
        flash("No entries in the last 7 days.", "error")
        return redirect(url_for("index"))

    start = today - timedelta(days=6)
    report = _build_report_dict("Weekly Mood Snapshot", counts, start, today)

    entries = _sorted_entries()
    summary = _streak_summary_for_ui()
    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        report=report,
        open_report_modal=True,
        open_view_modal=False,
        open_edit_modal=False,
    )


@app.get("/report/monthly")
def monthly_report():
    today = date.today()
    counts = mj.mj_monthly_report(today.day, today.month, today.year)
    if counts is None:
        flash("No entries in the last 30 days.", "error")
        return redirect(url_for("index"))

    start = today - timedelta(days=29)
    report = _build_report_dict("Monthly Mood Snapshot", counts, start, today)

    entries = _sorted_entries()
    summary = _streak_summary_for_ui()
    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        report=report,
        open_report_modal=True,
        open_view_modal=False,
        open_edit_modal=False,
    )


# ---------- Calendar + Mood Graph ----------

@app.get("/calendar")
def calendar_view():
    """Basic timeline/calendar: show entries grouped by date for the current month."""
    today = date.today()
    cal = mj.mj_month_calendar(today.year, today.month)
    entries = _sorted_entries()
    summary = _streak_summary_for_ui()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        calendar=cal,
        password_set=(ENTRY_PASSWORD is not None),
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
    )


@app.get("/mood-graph")
def mood_graph():
    """
    Mood rating graph:
    - mode=line : average mood per day (last 14 days)
    - mode=bar  : rating frequency histogram (1–100) over last 14 days
    """
    today = date.today()
    start = today - timedelta(days=13)
    mode = request.args.get("mode", "line")
    if mode not in ("line", "bar"):
        mode = "line"

    if mode == "bar":
        graph_dict = mj.mj_mood_rating_graph("bar", start, today)
        labels = list(range(1, 101))
        values = [graph_dict.get(i, 0) for i in labels]
    else:
        graph_dict = mj.mj_mood_rating_graph("line", start, today)
        # keys are dates; keep them ordered
        ordered_items = sorted(graph_dict.items(), key=lambda kv: kv[0])
        labels = [d.isoformat() for d, _ in ordered_items]
        values = [v for _, v in ordered_items]

    entries = _sorted_entries()
    summary = _streak_summary_for_ui()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        mood_graph_labels=labels,
        mood_graph_values=values,
        mood_graph_mode=mode,
        password_set=(ENTRY_PASSWORD is not None),
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
    )


if __name__ == "__main__":
    app.run(debug=True)
