"""Combines Signal 1 (UCW%) and Signal 2 (LLM label) into an AI-confidence score.

The score is the estimated probability that the content is AI-generated (0 to 1).

The LLM label is the primary signal and UCW% adjusts it, so that:
  - High UCW% + LLM "Human" leans human, since people can write with uncommon words
    (poetry, lyrics, formal writing).
  - Low UCW% + LLM "AI" still leans AI, since people often edit generated text to
    sound more natural.
"""
from signals.uncommon_words import DEFAULT_THRESHOLD

LLM_WEIGHT = 0.75
UCW_WEIGHT = 0.25

# UCW% at which Signal 1 counts as fully AI-like (twice the Signal 1 threshold).
UCW_SATURATION = DEFAULT_THRESHOLD * 2

# Labelling it AI has to clear a higher bar than labelling it human, to avoid
# wrongly flagging human writers. A score of 0.6 is not enough for "Likely AI".
LIKELY_AI_MIN = 0.70
LIKELY_HUMAN_MAX = 0.35


def ucw_strength(ucw_percent):
    """Scale UCW% to 0..1, reaching 1 at UCW_SATURATION."""
    return min(ucw_percent / UCW_SATURATION, 1.0)


def llm_ai_probability(llm):
    """Turn the LLM label + confidence into a probability of AI. Neutral if unavailable."""
    if not llm.get("available"):
        return 0.5
    if llm["label"] == "AI":
        return llm["confidence"]
    return 1.0 - llm["confidence"]


def confidence_score(ucw, llm):
    score = LLM_WEIGHT * llm_ai_probability(llm) + UCW_WEIGHT * ucw_strength(ucw["ucw_percent"])
    return round(score, 4)


def label_for(score):
    if score >= LIKELY_AI_MIN:
        return "Likely AI"
    if score <= LIKELY_HUMAN_MAX:
        return "Likely Human"
    return "Uncertain"


DISCLAIMER = (
    "This is an automated estimate and can be wrong. "
    "If you created this content, you can appeal this label."
)


def reader_label(score):
    """Plain-language version of the label and confidence for readers on the platform."""
    label = label_for(score)
    if label == "Uncertain":
        return {
            "label": label,
            "headline": "We can't tell if this was written by a person or by AI",
            "confidence_level": "Low",
            "confidence_text": "Our checks gave mixed results, so we aren't making a call either way.",
            "disclaimer": DISCLAIMER,
        }

    # How sure we are of the label shown, on the reader's side of the scale
    certainty = score if label == "Likely AI" else 1 - score
    high = certainty >= 0.85
    strength = "very likely" if high else "likely"
    if label == "Likely AI":
        headline = f"This content was {strength} created with AI"
    else:
        headline = f"This content was {strength} written by a person"
    return {
        "label": label,
        "headline": headline,
        "confidence_level": "High" if high else "Moderate",
        "confidence_text": (
            "Our checks strongly agree on this." if high
            else "Our checks lean this way, but not strongly."
        ),
        "disclaimer": DISCLAIMER,
    }
