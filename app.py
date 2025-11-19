from datetime import date, datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from mood_mastery.mood_journal import Mood_Journal
from mood_mastery.entry import BIOMETRICS, Entry

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-key"  # TODO: replace with env var in real deployment

# In-memory journal instance
mj = Mood_Journal()

# ----------------- THEME CONFIG -----------------

THEME_CHOICES = {
    "indigo": {
        "label": "Indigo",
        "accent": "79 70 229",
        "accent_soft": "165 180 252",
        "bg": "15 23 42",
        "bg_soft": "30 41 59",
        "card": "15 23 42",
    },
    "emerald": {
        "label": "Emerald",
        "accent": "16 185 129",
        "accent_soft": "167 243 208",
        "bg": "6 78 59",
        "bg_soft": "5 46 40",
        "card": "6 95 70",
    },
    "rose": {
        "label": "Rose",
        "accent": "244 63 94",
        "accent_soft": "254 202 202",
        "bg": "76 29 49",
        "bg_soft": "88 28 45",
        "card": "136 19 55",
    },
    "amber": {
        "label": "Amber",
        "accent": "245 158 11",
        "accent_soft": "253 230 138",
        "bg": "113 63 18",
        "bg_soft": "120 53 15",
        "card": "146 64 14",
    },
}

DEFAULT_THEME_KEY = "indigo"
THEME_SESSION_KEY = "mj_theme"


@app.context_processor
def inject_theme():
    theme_key = session.get(THEME_SESSION_KEY, DEFAULT_THEME_KEY)
    theme = THEME_CHOICES.get(theme_key, THEME_CHOICES[DEFAULT_THEME_KEY])
    return {
        "current_theme": theme,
        "current_theme_key": theme_key,
        "theme_choices": THEME_CHOICES,
    }


@app.post("/theme")
def set_theme():
    key = request.form.get("theme", DEFAULT_THEME_KEY)
    if key not in THEME_CHOICES:
        key = DEFAULT_THEME_KEY
    session[THEME_SESSION_KEY] = key
    return redirect(request.referrer or url_for("index"))


# ----------------- JINJA HELPERS -----------------


def ranking_emoji(r: int) -> str:
    """
    Convenience wrapper so templates can call ranking_emoji(r).
    Uses Entry.determine_ranking_emoji internally.
    """
    tmp = Entry("tmp", 1, 1, 2000, "", r, 50)
    return tmp.determine_ranking_emoji()


app.jinja_env.globals["ranking_emoji"] = ranking_emoji
app.jinja_env.globals["BIOMETRICS"] = BIOMETRICS

# Simple global password for demo
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
    entries.sort(
        key=lambda e: (
            e.entry_date,
            getattr(e, "entry_id_str", ""),
        ),
        reverse=True,
    )
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


# ----------------- TAG ORGANIZER CONTEXT -----------------


def _tag_context(selected_tag: str | None = None) -> dict:
    """
    Common context for the tag organizer UI in index.html.
    - all_tags: list of all unique tags (sorted)
    - tag_summary: list[(tag, count)] sorted by usage
    - tag_entries: entries matching a selected tag (or None if no tag)
    - selected_tag: normalized tag string, or None
    """
    all_tags = mj.mj_all_tags()
    tag_summary = mj.mj_tag_summary()

    # tag can come from argument or query param ?tag=...
    tag_param = selected_tag or request.args.get("tag", "").strip()
    tag_entries = None
    norm_tag = None

    if tag_param:
        norm_tag = tag_param.strip()
        tag_entries = mj.mj_entries_with_tag(norm_tag)

    return {
        "all_tags": all_tags,
        "tag_summary": tag_summary,
        "tag_entries": tag_entries,
        "selected_tag": norm_tag,
    }


# =========================================================
# Routes
# =========================================================


@app.route("/")
def index():
    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
        **tag_ctx,
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
    tag_ctx = _tag_context()

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
        **tag_ctx,
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

    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

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
        **tag_ctx,
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
    tag_ctx = _tag_context()

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
        **tag_ctx,
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
    tag_ctx = _tag_context()

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
        **tag_ctx,
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
    tag_ctx = _tag_context()

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
        **tag_ctx,
    )


# ---------- Calendar + Mood Graph ----------


@app.get("/calendar")
def calendar_view():
    """
    Show one full month containing 'today', grouped by date.
    """
    today = date.today()
    cal = mj.mj_month_calendar(today.year, today.month)
    entries = _sorted_entries()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

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
        **tag_ctx,
    )


@app.get("/mood-graph")
def mood_graph():
    """
    Mood rating graph (line or bar) for the last 14 days.
    """
    mode = request.args.get("mode", "line")
    if mode not in ("line", "bar"):
        mode = "line"

    today = date.today()
    start = today - timedelta(days=13)
    data_dict = mj.mj_mood_rating_graph(mode, start, today)

    if mode == "line":
        # keys are date objects
        days_sorted = sorted(data_dict.keys())
        labels = [d.isoformat() for d in days_sorted]
        values = [data_dict[d] for d in days_sorted]
    else:
        # bar: keys are 1..100 (ratings), but we don't assume they're all present
        labels = list(range(1, 101))
        values = [data_dict.get(i, 0) for i in labels]

    entries = _sorted_entries()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

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
        **tag_ctx,
    )

# ---------- Emoji Groups Report ----------

@app.get("/emoji-groups")
def emoji_groups():
    """Show all emoji groups with distribution"""
    emoji_data = {}
    
    # Get data for all emojis (1-5 rankings)
    for emoji_rank in range(1, 6):
        rating_count, entry_keys = mj.mj_emoji_groups(emoji_rank)
        total_entries = sum(rating_count)
        
        # Only include emojis that have entries
        if total_entries > 0:
            # Create distribution bars
            distribution = []
            for rating in range(100):
                count = rating_count[rating]
                if count > 0:
                    pct = (count / total_entries) * 100
                    distribution.append({
                        'rating': rating + 1,
                        'count': count,
                        'pct': round(pct, 1)
                    })
            
            emoji_data[emoji_rank] = {
                'emoji': ranking_emoji(emoji_rank),
                'total_entries': total_entries,
                'distribution': distribution,
                'entry_keys': entry_keys
            }

    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        emoji_groups_data=emoji_data,
        open_emoji_groups_modal=True,
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
        **tag_ctx,
    )


@app.get("/emoji-groups/<int:emoji_rank>")
def emoji_group_detail(emoji_rank):
    """Show detailed view for a specific emoji group"""
    if emoji_rank < 1 or emoji_rank > 5:
        flash("Invalid emoji rank.", "error")
        return redirect(url_for("emoji_groups"))

    rating_count, entry_keys = mj.mj_emoji_groups(emoji_rank)
    total_entries = sum(rating_count)
    
    if total_entries == 0:
        flash(f"No entries found for {ranking_emoji(emoji_rank)} emoji.", "error")
        return redirect(url_for("emoji_groups"))

    # Get the actual entry objects for the keys
    emoji_entries = []
    for key in entry_keys:
        entry = mj.mj_get_entry(key)
        if entry:
            emoji_entries.append(entry)
    
    # Sort entries by date (newest first)
    emoji_entries.sort(key=lambda e: e.entry_date, reverse=True)
    
    # Create distribution data
    distribution = []
    for rating in range(100):
        count = rating_count[rating]
        if count > 0:
            pct = (count / total_entries) * 100
            distribution.append({
                'rating': rating + 1,
                'count': count,
                'pct': round(pct, 1)
            })

    entries = _sorted_entries()
    today = date.today()
    summary = _streak_summary_for_ui()
    tag_ctx = _tag_context()

    return render_template(
        "index.html",
        entries=entries,
        today=today,
        summary=summary,
        password_set=(ENTRY_PASSWORD is not None),
        emoji_group_detail={
            'rank': emoji_rank,
            'emoji': ranking_emoji(emoji_rank),
            'total_entries': total_entries,
            'distribution': distribution,
            'emoji_entries': emoji_entries
        },
        open_emoji_group_detail_modal=True,
        open_emoji_groups_modal=False,
        open_view_modal=False,
        open_edit_modal=False,
        open_report_modal=False,
        **tag_ctx,
    )

if __name__ == "__main__":
    app.run(debug=True)
