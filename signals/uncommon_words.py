"""Signal 1: Uncommon Word (UCW) check.

Counts words that are uncommon in everyday human writing but show up often in
AI-generated text, and divides by the passage's total word count.
"""
import re

# Words that are rare in casual human writing but common in LLM output.
# Inflected forms are listed explicitly so matching stays a simple set lookup.
UNCOMMON_WORDS = frozenset({
    "delve", "delves", "delving", "delved",
    "tapestry", "tapestries",
    "multifaceted",
    "intricate", "intricacies",
    "nuanced", "nuances",
    "pivotal",
    "realm", "realms",
    "testament",
    "underscore", "underscores", "underscoring", "underscored",
    "showcase", "showcases", "showcasing", "showcased",
    "foster", "fosters", "fostering", "fostered",
    "leverage", "leverages", "leveraging", "leveraged",
    "seamless", "seamlessly",
    "robust",
    "holistic",
    "paramount",
    "meticulous", "meticulously",
    "commendable",
    "embark", "embarks", "embarking", "embarked",
    "navigate", "navigates", "navigating",
    "landscape",
    "bustling",
    "vibrant",
    "furthermore", "moreover", "additionally",
    "notably",
    "crucial",
    "elevate", "elevates", "elevating",
    "harness", "harnessing",
    "unwavering",
    "enigmatic",
    "symphony",
    "beacon",
    "transformative",
    "resonate", "resonates", "resonating",
    "ever-evolving",
    "intricately",
    "comprehensive",
    "invaluable",
    "captivating",
    "endeavor", "endeavors", "endeavour", "endeavours",
})

# Starting threshold: passages above 3% UCW lean AI. Tune against real samples.
DEFAULT_THRESHOLD = 0.03

_WORD_RE = re.compile(r"[a-z]+(?:[-'][a-z]+)*")


def tokenize(text):
    return _WORD_RE.findall(text.lower())


def ucw_signal(text, threshold=DEFAULT_THRESHOLD):
    """Return the UCW ratio for `text` and whether it crosses `threshold`."""
    words = tokenize(text)
    total = len(words)
    matches = [w for w in words if w in UNCOMMON_WORDS]
    ratio = len(matches) / total if total else 0.0
    return {
        "ucw_percent": round(ratio, 4),
        "uncommon_count": len(matches),
        "total_words": total,
        "matched_words": sorted(set(matches)),
        "above_threshold": ratio > threshold,
    }
