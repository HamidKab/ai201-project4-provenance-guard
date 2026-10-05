import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from scoring import confidence_score, label_for, reader_label
from signals.llm_classifier import llm_signal
from signals.uncommon_words import ucw_signal
from submission_log import read_entries, write_entry

load_dotenv()

DEFAULT_LOG_LIMIT = 50
MAX_LOG_LIMIT = 500

app = Flask(__name__)
app.config["SUBMISSION_LOG_PATH"] = "logs/submissions.jsonl"
app.config["APPEAL_LOG_PATH"] = "logs/appeals.jsonl"

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")


@app.route("/submit", methods=["POST"])
@limiter.limit("5 per minute;100 per day")
def submit():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    text = data.get("text")
    creator_id = data.get("creator_id")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "'text' is required and must be a non-empty string"}), 400
    if not isinstance(creator_id, str) or not creator_id.strip():
        return jsonify({"error": "'creator_id' is required and must be a non-empty string"}), 400

    content_id = str(uuid.uuid4())
    ucw = ucw_signal(text)
    llm = llm_signal(text)
    confidence = confidence_score(ucw, llm)
    label = label_for(confidence)

    write_entry(app.config["SUBMISSION_LOG_PATH"], {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": label,
        "confidence": confidence,
        "signal_1_ucw_percent": ucw["ucw_percent"],
        "signal_2_llm_label": llm["label"],
        "signal_2_llm_confidence": llm["confidence"],
    })

    return jsonify({
        "content_id": content_id,
        "creator_id": creator_id,
        "label": label,
        "confidence": confidence,
        "reader_label": reader_label(confidence),
        "signals": {"ucw": ucw, "llm": llm},
    }), 200


@app.route("/log", methods=["GET"])
def get_log():
    raw_limit = request.args.get("limit", str(DEFAULT_LOG_LIMIT))
    if not raw_limit.isdigit() or int(raw_limit) < 1:
        return jsonify({"error": "'limit' must be a positive integer"}), 400
    limit = int(raw_limit)
    limit = min(limit, MAX_LOG_LIMIT)

    entries = read_entries(app.config["SUBMISSION_LOG_PATH"])
    recent = entries[-limit:][::-1]  # newest first
    return jsonify({"count": len(recent), "entries": recent}), 200


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")
    evidence = data.get("evidence")
    if not isinstance(content_id, str) or not content_id.strip():
        return jsonify({"error": "'content_id' is required and must be a non-empty string"}), 400
    if not isinstance(reasoning, str) or not reasoning.strip():
        return jsonify({"error": "'creator_reasoning' is required and must be a non-empty string"}), 400
    if evidence is not None and not isinstance(evidence, str):
        return jsonify({"error": "'evidence' must be a string if provided"}), 400

    original = next(
        (e for e in read_entries(app.config["SUBMISSION_LOG_PATH"]) if e["content_id"] == content_id),
        None,
    )
    if original is None:
        return jsonify({"error": "No submission found for that content_id"}), 404
    if any(a["content_id"] == content_id for a in read_entries(app.config["APPEAL_LOG_PATH"])):
        return jsonify({"error": "This content is already under review"}), 409

    # Logged alongside the original classification; status changes, label does not
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content_id": content_id,
        "creator_reasoning": reasoning,
        "evidence": evidence,
        "original_classification": original,
        "status": "Under Review",
    }
    write_entry(app.config["APPEAL_LOG_PATH"], entry)
    return jsonify(entry), 201


if __name__ == "__main__":
    app.run(debug=True)
