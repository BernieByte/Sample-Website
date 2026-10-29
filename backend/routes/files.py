from flask import Blueprint, jsonify, request, session

from backend.db import get_db
from backend.utils import sanitize_document_html


files_bp = Blueprint("files", __name__, url_prefix="/api")
MAX_DOCUMENT_CHARACTERS = 1_000_000


def serialize_file(file_item):
    item = dict(file_item)
    item["content"] = sanitize_document_html(item.get("content") or "")
    return item


@files_bp.before_request
def require_login():
    if request.endpoint and request.endpoint.startswith("files."):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401


@files_bp.route("/files", methods=["POST"])
def create_file():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled").strip()
    content = data.get("content") or ""

    if not isinstance(content, str):
        return jsonify({"error": "Document content must be text."}), 400
    if len(content) > MAX_DOCUMENT_CHARACTERS:
        return jsonify({"error": "This document is too large to save."}), 413
    content = sanitize_document_html(content)

    if not title:
        return jsonify({"error": "Title is required."}), 400

    db = get_db()
    if db.postgres:
        file_id = db.execute(
            "INSERT INTO files (user_id, title, content) VALUES (?, ?, ?) RETURNING id",
            (session["user_id"], title, content),
        ).fetchone()["id"]
    else:
        db.execute(
            "INSERT INTO files (user_id, title, content) VALUES (?, ?, ?)",
            (session["user_id"], title, content),
        )
        file_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    return jsonify({"message": "File created successfully.", "file": serialize_file(file_item)}), 201


@files_bp.route("/files", methods=["GET"])
def list_files():
    db = get_db()
    files = db.execute(
        "SELECT * FROM files WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
        (session["user_id"],),
    ).fetchall()
    return jsonify({"files": [serialize_file(file_item) for file_item in files]}), 200


@files_bp.route("/files/<int:file_id>", methods=["GET"])
def get_file(file_id):
    db = get_db()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not file_item:
        return jsonify({"error": "File not found."}), 404

    return jsonify({"file": serialize_file(file_item)}), 200


@files_bp.route("/files/<int:file_id>", methods=["PUT"])
def update_file(file_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = data.get("content")

    if content is not None and not isinstance(content, str):
        return jsonify({"error": "Document content must be text."}), 400
    if content is not None and len(content) > MAX_DOCUMENT_CHARACTERS:
        return jsonify({"error": "This document is too large to save."}), 413

    db = get_db()
    file_item = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not file_item:
        return jsonify({"error": "File not found."}), 404

    if title:
        file_item_title = title
    else:
        file_item_title = file_item["title"]

    if content is None:
        file_item_content = file_item["content"]
    else:
        file_item_content = sanitize_document_html(content)

    db.execute(
        "UPDATE files SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (file_item_title, file_item_content, file_id, session["user_id"]),
    )
    db.commit()

    updated = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    return jsonify({"message": "File updated successfully.", "file": serialize_file(updated)}), 200


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
            "INSERT INTO files (user_id, title, content) VALUES (?, ?, ?) RETURNING id",
            (session["user_id"], title, sanitize_document_html(source["content"] or "")),
        ).fetchone()["id"]
    else:
        db.execute(
            "INSERT INTO files (user_id, title, content) VALUES (?, ?, ?)",
            (session["user_id"], title, sanitize_document_html(source["content"] or "")),
        )
        new_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()
    duplicate = db.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (new_id, session["user_id"]),
    ).fetchone()
    return jsonify({"message": "File duplicated successfully.", "file": serialize_file(duplicate)}), 201


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
