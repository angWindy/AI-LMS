"""Helpers for adapting prompts to course learning levels."""

COURSE_LEVEL_LABELS = {
    "primary": "Primary school",
    "lower_secondary": "Lower secondary (middle school)",
    "upper_secondary": "Upper secondary (high school)",
    "higher_ed": "Higher education and postgraduate",
}

COURSE_LEVEL_GUIDANCE = {
    "primary": [
        "Use very simple language and short sentences.",
        "Prefer concrete, daily-life examples and step-by-step guidance.",
        "Avoid abstract theory, heavy formulas, or jargon unless explained.",
        "Ask short check-in questions to confirm understanding.",
    ],
    "lower_secondary": [
        "Use clear, age-appropriate language with brief definitions for new terms.",
        "Balance concrete examples with light conceptual explanations.",
        "Keep reasoning short and avoid advanced proofs.",
    ],
    "upper_secondary": [
        "Use standard academic Vietnamese with concise explanations.",
        "Include moderate reasoning, comparisons, and structured steps.",
        "Use formulas or formal terms when needed, with brief reminders.",
    ],
    "higher_ed": [
        "Use precise academic language and allow deeper analysis.",
        "Assume foundational knowledge; focus on rigor and nuance.",
        "Allow formal definitions, proofs, or advanced terminology when relevant.",
    ],
}


def _normalize_level(level: str | None) -> str | None:
    if not level:
        return None
    normalized = level.strip().lower()
    return normalized if normalized in COURSE_LEVEL_LABELS else None


def build_learning_level_instructions(level: str | None) -> str:
    """Return a prompt section that adapts to the learner's level."""
    normalized = _normalize_level(level)
    if not normalized:
        return (
            "Learner level: Unknown. Use clear, neutral Vietnamese, avoid"
            " overly advanced jargon, and keep explanations concise."
        )

    label = COURSE_LEVEL_LABELS[normalized]
    guidance = COURSE_LEVEL_GUIDANCE.get(normalized, [])
    lines = [
        f"Learner level: {label}.",
        "Adapt vocabulary, depth, pacing, and examples to this level.",
    ]
    lines.extend(f"- {item}" for item in guidance)
    return "\n".join(lines)
