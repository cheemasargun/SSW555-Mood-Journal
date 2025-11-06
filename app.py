from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
import os

# Import your classes
from mood_mastery.user import User
# Import BIOMETRICS map from your Entry module so we can render choices
try:
    from mood_mastery.entry import BIOMETRICS
except Exception:
    from entry import BIOMETRICS  # type: ignore

app = Flask(__name__)
app.secret_key = os.environ.get("MOOD_DEMO_SECRET", "dev-secret")

# Single demo user (in-memory)
user = User()

# -------- Helpers --------
def ranking_emoji(rank: int) -> str:
    mapping = {
        1: "😵", 2: "😖", 3: "🙁", 4: "😢",
        5: "😡", 6: "😐", 7: "🙂", 8: "😄",
    }
    try:
        return mapping.get(int(rank), "🙂")
    except Exception:
        return "🙂"

@app.context_processor
def inject_helpers():
    # expose helpers & BIOMETRICS to templates
    return dict(ranking_emoji=ranking_emoji, BIOMETRICS=BIOMETRICS)

def get_today():
    t = date.today()
    return {"year": t.year, "month": t.month, "day": t.day}

def _render_index(**extra):
    entries = user.user_mood_journal.mj_get_all_entries()
    entries.sort(key=lambda e: (e.entry_date, e.entry_name), reverse=True)
    s = user.user_mood_journal.get_streak_summary()
    summary = {
        "current": s["current_streak"],
        "longest": s["longest_streak"],
        "last": s["last_entry_date"].isoformat() if s["last_entry_date"] else None,
    }
    base_ctx = dict(
        entries=entries,
        summary=summary,
        today=get_today(),
        password_set=(user.user_entries_pwd_encrypted is not None),
    )
    base_ctx.update(extra)
    return render_template("apps/mood_journal/index.html", **base_ctx)

def _open_view_modal(entry_id, body=None, ask_password=False):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    return _render_index(
        view_e=e,
        view_body=body,
        view_ask_password=ask_password,
        open_view_modal=True,
    )

def _open_edit_modal(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    return _render_index(
        edit_e=e,
        open_edit_modal=True,
    )

def _parse_biometrics_form(form):
    """Collect biometrics from form fields named bio_<Category>."""
    data = {}
    for key, choices in BIOMETRICS.items():
        val = form.get(f"bio_{key}", "").strip()
        if val and val in choices:
            data[key] = val
    return data

# -------- Routes --------
@app.route("/")
def index():
    return _render_index()

@app.route("/add", methods=["POST"])
def add_entry():
    f = request.form
    try:
        title = f.get("title", "Untitled").strip()
        year = int(f.get("year")); month = int(f.get("month")); day = int(f.get("day"))
        ranking = int(f.get("ranking", 5))
        body = f.get("body", "").strip()
        tags_raw = f.get("tags", "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else None

        biometrics = _parse_biometrics_form(f)

        user.user_mood_journal.mj_log_entry(
            entry_name=title,
            entry_day=day,
            entry_month=month,
            entry_year=year,
            entry_body=body,
            ranking=ranking,
            tags=tags,
            biometrics=biometrics,  # <- fixed: no duplicate 'tags' kwarg
        )
        flash("Entry created!", "success")
    except Exception as ex:
        flash(f"Failed to create entry: {ex}", "error")
    return redirect(url_for("index"))

# Optional mirror if something posts to /mood-journal
@app.route("/mood-journal", methods=["POST"])
def add_entry_mirror():
    return add_entry()

# ---- VIEW (separate) ----
@app.route("/entry/<entry_id>")
def view_entry(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    obj = user.view_entry(entry_id)  # Entry or False (if private)
    body = obj.entry_body if obj and hasattr(obj, "entry_body") else None
    ask_password = (body is None) and e.is_private_check()
    return _open_view_modal(entry_id, body=body, ask_password=ask_password)

@app.route("/entry/<entry_id>/unlock", methods=["POST"])
def unlock_entry(entry_id):
    pwd = request.form.get("password", "")
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    obj = user.view_entry(entry_id, entry_pwd_attempt=pwd)
    if obj is False:
        flash("Incorrect password.", "error")
        return _open_view_modal(entry_id, body=None, ask_password=True)
    return _open_view_modal(entry_id, body=obj.entry_body, ask_password=False)

@app.route("/privacy/<entry_id>", methods=["POST"])
def make_private(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    if user.user_entries_pwd_encrypted is None:
        pwd = request.form.get("password")
        if not pwd:
            flash("Create a password to enable privacy.", "error")
            return _open_view_modal(entry_id, body=None, ask_password=True)
        ok = user.privatize_entry(entry_id_str=entry_id, user_entries_pwd=pwd)
    else:
        ok = user.privatize_entry(entry_id_str=entry_id)

    flash("Entry set to private." if ok else "Could not set privacy.", "success" if ok else "error")
    return _open_view_modal(entry_id, body=None, ask_password=True if ok else False)

@app.route("/delete/<entry_id>", methods=["POST"])
def delete_entry(entry_id):
    if user.user_mood_journal.mj_delete_entry(entry_id):
        flash("Entry deleted.", "success")
    else:
        flash("Could not delete entry.", "error")
    return redirect(url_for("index"))

# ---- EDIT (separate) ----
@app.route("/entry/<entry_id>/edit")
def edit_entry_open(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    return _open_edit_modal(entry_id)

@app.route("/entry/<entry_id>/edit", methods=["POST"])
def edit_entry_save(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))

    f = request.form
    try:
        new_title = f.get("title", e.entry_name).strip() or e.entry_name
        new_year = int(f.get("year", e.entry_date.year))
        new_month = int(f.get("month", e.entry_date.month))
        new_day = int(f.get("day", e.entry_date.day))
        new_body = f.get("body", e.entry_body)
        new_rank = int(f.get("ranking", e.ranking))

        user.user_mood_journal.mj_edit_entry(
            entry_id_str=entry_id,
            new_name=new_title,
            new_day=new_day,
            new_month=new_month,
            new_year=new_year,
            new_body=new_body,
            new_ranking=new_rank
        )

        # Biometrics update (only fields the user chose)
        bio_updates = _parse_biometrics_form(f)
        for k, v in bio_updates.items():
            e.set_biometric(k, v)

        flash("Entry updated.", "success")
    except Exception as ex:
        flash(f"Failed to update entry: {ex}", "error")

    return _open_edit_modal(entry_id)

# ---- TAGS (on the Edit feature) ----
@app.route("/entry/<entry_id>/tags/add", methods=["POST"])
def add_tag(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    tag = (request.form.get("tag") or "").strip()
    if not tag:
        flash("Tag cannot be empty.", "error")
    elif e.add_tag(tag):
        flash(f"Tag “{tag}” added.", "success")
    else:
        flash(f"Tag “{tag}” already exists or invalid.", "error")
    return _open_edit_modal(entry_id)

@app.route("/entry/<entry_id>/tags/delete", methods=["POST"])
def delete_tag(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    tag = (request.form.get("tag") or "").strip()
    if e.remove_tag(tag):
        flash(f"Tag “{tag}” removed.", "success")
    else:
        flash(f"Tag “{tag}” not found.", "error")
    return _open_edit_modal(entry_id)

@app.route("/entry/<entry_id>/tags/clear", methods=["POST"])
def clear_tags(entry_id):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    e.clear_tags()
    flash("All tags cleared.", "success")
    return _open_edit_modal(entry_id)

# ---- BIOMETRICS (edit feature) ----
@app.route("/entry/<entry_id>/biometrics/clear/<key>", methods=["POST"])
def clear_biometric(entry_id, key):
    e = user.user_mood_journal.mj_get_entry(entry_id)
    if not e:
        flash("Entry not found.", "error")
        return redirect(url_for("index"))
    try:
        from mood_mastery.entry import BIOMETRICS as _BIO
    except Exception:
        try:
            from entry import BIOMETRICS as _BIO  # type: ignore
        except Exception:
            _BIO = BIOMETRICS
    if key in _BIO and e.delete_biometric(key):
        flash(f"Cleared “{key}”.", "success")
    else:
        flash("Nothing to clear.", "error")
    return _open_edit_modal(entry_id)

if __name__ == "__main__":
    app.run(debug=True)
