"""Structured submission log, written as JSON Lines (one JSON object per line)."""
import json
import os
import threading

_lock = threading.Lock()


def write_entry(path, entry):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with _lock, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_entries(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
