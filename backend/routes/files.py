from flask import Blueprint, jsonify, request, session

from backend.db import get_db


files_bp = Blueprint("files", __name__, url_prefix="/api")


@files_bp.before_request
def require_login():
    if request.endpoint in {"files.create_file", "files.list_files", "files.get_file", "files.update_file", "files.delete_file"}:
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401


@files_bp.route("/files", methods=["POST"])
def create_file():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled").strip()
    folder = (data.get("folder") or "").strip()
    content = data.get("content") or ""

    if not title:
        return jsonify({"error": "Title is required."}), 400

    db = get_db()
    if db.postgres:
        file_id = db.execute(
            "INSERT INTO files (user_id, title, folder, content) VALUES (?, ?, ?, ?) RETURNING id",
            (session["user_id"], title, folder, content),
        ).fetchone()["id"]
    else:
        db.execute(
            "INSERT INTO files (user_id, title, folder, content) VALUES (?, ?, ?, ?)",
            (session["user_id"], title, folder, content),
        )
        file_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    return jsonify({"message": "File created successfully.", "file": dict(file_item)}), 201


@files_bp.route("/files", methods=["GET"])
def list_files():
    db = get_db()
    files = db.execute(
        "SELECT * FROM files WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
        (session["user_id"],),
    ).fetchall()
    return jsonify({"files": [dict(file_item) for file_item in files]}), 200


@files_bp.route("/files/<int:file_id>", methods=["GET"])
def get_file(file_id):
    db = get_db()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not file_item:
        return jsonify({"error": "File not found."}), 404

    return jsonify({"file": dict(file_item)}), 200


@files_bp.route("/files/<int:file_id>", methods=["PUT"])
def update_file(file_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = data.get("content")

    db = get_db()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not file_item:
        return jsonify({"error": "File not found."}), 404

    folder = (data.get("folder") or file_item["folder"] or "").strip()

    if title:
        file_item_title = title
    else:
        file_item_title = file_item["title"]

    if content is None:
        file_item_content = file_item["content"]
    else:
        file_item_content = content

    db.execute(
        "UPDATE files SET title = ?, folder = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (file_item_title, folder, file_item_content, file_id, session["user_id"]),
    )
    db.commit()

    updated = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    return jsonify({"message": "File updated successfully.", "file": dict(updated)}), 200


@files_bp.route("/files/<int:file_id>/duplicate", methods=["POST"])
def duplicate_file(file_id):
    db = get_db()
    source = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()
    if not source:
        return jsonify({"error": "File not found."}), 404

    title = f"Copy of {source['title']}"
    if db.postgres:
        new_id = db.execute(
            "INSERT INTO files (user_id, title, folder, content) VALUES (?, ?, ?, ?) RETURNING id",
            (session["user_id"], title, source["folder"], source["content"]),
        ).fetchone()["id"]
    else:
        db.execute(
            "INSERT INTO files (user_id, title, folder, content) VALUES (?, ?, ?, ?)",
            (session["user_id"], title, source["folder"], source["content"]),
        )
        new_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()
    duplicate = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (new_id, session["user_id"]),
    ).fetchone()
    return jsonify({"message": "File duplicated successfully.", "file": dict(duplicate)}), 201


@files_bp.route("/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    db = get_db()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not file_item:
        return jsonify({"error": "File not found."}), 404

    db.execute(
        "DELETE FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    )
    db.commit()

    return jsonify({"message": "File deleted successfully."}), 200
