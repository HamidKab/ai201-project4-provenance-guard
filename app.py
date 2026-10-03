from flask import Flask, jsonify, request

from signals.uncommon_words import ucw_signal

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
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

    ucw = ucw_signal(text)

    # Label and confidence are placeholders until Signal 2 (LLM) and scoring are added
    return jsonify({
        "creator_id": creator_id,
        "label": "Uncertain",
        "confidence": 0.5,
        "signals": {"ucw": ucw},
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
