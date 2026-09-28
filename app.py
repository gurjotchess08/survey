import os

import psycopg2
from flask import flask, jsonify, request

app = Flask(__name__)

LANGUAGES = {"Python", "C", "Java", "JavaScript", "Other"}


def get_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set in Vercel Environment Variables")
    return psycopg2.connect(url)


@app.get("/api/responses")
def list_responses():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, language, rating, comment, created_at "
                "FROM survey_responses ORDER BY id DESC"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify(
        [
            {
                "id": r[0],
                "name": r[1],
                "language": r[2],
                "rating": r[3],
                "comment": r[4],
                "created_at": r[5].strftime("%d %b %Y, %H:%M"),
            }
            for r in rows
        ]
    )


@app.post("/api/responses")
def add_response():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    language = str(data.get("language", "")).strip()
    comment = str(data.get("comment", "")).strip()
    
    try:
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        return jsonify({"error": "Rating must be a number from 1 to 5."}), 400

    if not name or len(name) > 60:
        return jsonify({"error": "Name is required (max 60 characters)."}), 400
    if language not in LANGUAGES:
        return jsonify({"error": "Pick a language from the list."}), 400
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be from 1 to 5."}), 400
    if len(comment) > 300:
        return jsonify({"error": "Comment is too long (max 300 characters)."}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO survey_responses (name, language, rating, comment) "
                "VALUES (%s, %s, %s, %s)",
                (name, language, rating, comment),
            )
        conn.commit()
    finally:
        conn.close()

     @app.get("/api/health")
def health():
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        return jsonify({"env": False})
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.survey_responses')")
            table = cur.fetchone()[0]
        conn.close()
        return jsonify({"env": True, "connected": True, "table": table})
    except Exception as e:
        return jsonify({"env": True, "connected": False, "error": type(e).__name__})
    
    return jsonify({"ok": True}), 201
