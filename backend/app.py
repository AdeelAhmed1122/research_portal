import os
from datetime import date, datetime

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db

FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
app = Flask(__name__, static_folder=None)

TEXT_LIMITS = {  # field -> max length
    "title": 200, "research_area": 100, "faculty_name": 100,
    "department": 100, "required_skills": 500,
}
LABELS = {
    "title": "Research title", "description": "Research description",
    "research_area": "Research area", "faculty_name": "Faculty member's name",
    "department": "Department", "required_skills": "Required skills",
    "positions": "Number of positions", "deadline": "Application deadline",
    "status": "Status",
}


def validate(data):
    """Return (clean_data, error_message). Exactly one of them is None."""
    clean = {}
    for f in ("title", "description", "research_area", "faculty_name",
              "department", "required_skills"):
        v = data.get(f)
        if not isinstance(v, str) or not v.strip():
            return None, f"{LABELS[f]} is required."
        v = v.strip()
        if f in TEXT_LIMITS and len(v) > TEXT_LIMITS[f]:
            return None, f"{LABELS[f]} must be at most {TEXT_LIMITS[f]} characters."
        clean[f] = v

    pos = data.get("positions")
    if isinstance(pos, bool) or pos in (None, ""):
        return None, f"{LABELS['positions']} is required."
    try:
        pos = int(pos)
    except (TypeError, ValueError):
        return None, f"{LABELS['positions']} must be a whole number."
    if pos < 1 or pos > 1000:
        return None, f"{LABELS['positions']} must be between 1 and 1000."
    clean["positions"] = pos

    dl = data.get("deadline")
    if not isinstance(dl, str) or not dl.strip():
        return None, f"{LABELS['deadline']} is required."
    try:
        clean["deadline"] = datetime.strptime(dl.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, f"{LABELS['deadline']} must be a valid date (YYYY-MM-DD)."

    status = data.get("status", "Open")
    if status not in ("Open", "Closed"):
        return None, "Status must be either Open or Closed."
    clean["status"] = status
    return clean, None


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def error(message, code):
    return jsonify({"error": message}), code


# ---------------- REST API ----------------
@app.post("/api/opportunities")
def create_opportunity():
    data = json_body()
    if data is None:
        return error("Request body must be valid JSON.", 400)
    clean, err = validate(data)
    if err:
        return error(err, 400)
    new_id = db.create(clean)
    return jsonify({"message": "Research opportunity created.",
                    "opportunity": db.get_one(new_id)}), 201


@app.get("/api/opportunities")
def list_opportunities():
    return jsonify(db.get_all()), 200


@app.get("/api/opportunities/<int:oid>")
def get_opportunity(oid):
    row = db.get_one(oid)
    if row is None:
        return error(f"Research opportunity {oid} was not found.", 404)
    return jsonify(row), 200


@app.put("/api/opportunities/<int:oid>")
def update_opportunity(oid):
    data = json_body()
    if data is None:
        return error("Request body must be valid JSON.", 400)
    existing = db.get_one(oid)
    if existing is None:
        return error(f"Research opportunity {oid} was not found.", 404)
    # Partial updates allowed: fields not sent keep their current value.
    merged = {f: existing[f] for f in db.FIELDS}
    merged.update({k: v for k, v in data.items() if k in db.FIELDS})
    clean, err = validate(merged)
    if err:
        return error(err, 400)
    db.update(oid, clean)
    return jsonify({"message": "Research opportunity updated.",
                    "opportunity": db.get_one(oid)}), 200


@app.delete("/api/opportunities/<int:oid>")
def delete_opportunity(oid):
    if not db.delete(oid):
        return error(f"Research opportunity {oid} was not found.", 404)
    return jsonify({"message": "Research opportunity deleted."}), 200


# ---------------- error handlers (always JSON for /api) ----------------
@app.errorhandler(HTTPException)
def http_error(e):
    if request.path.startswith("/api/"):
        return error(e.description if e.code != 404 else "Resource not found.", e.code)
    return e


@app.errorhandler(Exception)
def server_error(e):
    app.logger.exception("Unhandled error")
    return error("Internal server error. Please try again later.", 500)


# ---------------- frontend ----------------
@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:name>")
def assets(name):
    return send_from_directory(FRONTEND, name)


if __name__ == "__main__":
    db.init_db()  # local development only: also creates the database
    app.run(debug=True, port=5000)
