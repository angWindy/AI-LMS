"""Course learning-level helpers for LLM prompts."""

DEFAULT_LEARNING_LEVEL = "higher_education"

LEARNING_LEVELS = {
    "elementary": {
        "label": "Tiểu học",
        "guidance": (
            "Use very simple Vietnamese, concrete examples, short sentences, "
            "small steps, and avoid abstract terminology unless it is explained immediately."
        ),
    },
    "middle_school": {
        "label": "Trung học cơ sở",
        "guidance": (
            "Use age-appropriate Vietnamese, explain new terms before using them, "
            "connect ideas to familiar situations, and keep reasoning scaffolded."
        ),
    },
    "high_school": {
        "label": "Trung học phổ thông",
        "guidance": (
            "Use standard academic Vietnamese, include definitions and examples, "
            "and require application, comparison, and structured reasoning where appropriate."
        ),
    },
    "higher_education": {
        "label": "Đại học và sau đại học",
        "guidance": (
            "Use precise academic Vietnamese, preserve technical vocabulary, "
            "support deeper analysis, and expect independent reasoning from the learner."
        ),
    },
}

_ALIASES = {
    "elementary": "elementary",
    "primary": "elementary",
    "tieu_hoc": "elementary",
    "tieu hoc": "elementary",
    "tiểu học": "elementary",
    "middle_school": "middle_school",
    "secondary": "middle_school",
    "junior_high": "middle_school",
    "thcs": "middle_school",
    "trung hoc co so": "middle_school",
    "trung học cơ sở": "middle_school",
    "high_school": "high_school",
    "senior_high": "high_school",
    "thpt": "high_school",
    "trung hoc pho thong": "high_school",
    "trung học phổ thông": "high_school",
    "higher_education": "higher_education",
    "university": "higher_education",
    "college": "higher_education",
    "graduate": "higher_education",
    "dai hoc va sau dai hoc": "higher_education",
    "đại học và sau đại học": "higher_education",
    "beginner": DEFAULT_LEARNING_LEVEL,
    "intermediate": DEFAULT_LEARNING_LEVEL,
    "advanced": DEFAULT_LEARNING_LEVEL,
}


def normalize_learning_level(level: str | None) -> str | None:
    """Normalize API/DB learning-level values into canonical prompt keys."""
    if level is None:
        return None
    raw = str(level).strip()
    if not raw:
        return None
    key = raw.lower().replace("-", "_")
    return _ALIASES.get(key, _ALIASES.get(raw.lower(), DEFAULT_LEARNING_LEVEL))


def learning_level_label(level: str | None) -> str:
    """Return the Vietnamese display label for a learning level."""
    normalized = normalize_learning_level(level)
    if normalized is None:
        return "Chưa xác định"
    return LEARNING_LEVELS[normalized]["label"]


def learning_level_guidance(level: str | None) -> str:
    """Return concise prompt guidance for adapting to a learning level."""
    normalized = normalize_learning_level(level)
    if normalized is None:
        return (
            "Use a neutral LMS tutor style, ask clarifying questions when the "
            "expected learner level is important, and avoid unnecessary complexity."
        )
    return LEARNING_LEVELS[normalized]["guidance"]


def build_learning_level_prompt_block(level: str | None) -> str:
    """Build a prompt block shared by all LMS LLM services."""
    normalized = normalize_learning_level(level) or "unknown"
    label = learning_level_label(level)
    guidance = learning_level_guidance(level)
    return "\n".join(
        [
            f"Learner level: {label} ({normalized})",
            f"Level adaptation guidance: {guidance}",
            "Keep the content academically correct; adapt explanation depth, vocabulary, examples, and scaffolding to this learner level.",
        ]
    )
