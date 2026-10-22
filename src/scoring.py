
"""Pengiraan padanan kerjaya dan laluan pembelajaran."""

W_SKILL = 0.6
W_TREND = 0.4

DEFAULT_TREND = 0.5
SCENARIOS = ("moderate", "fast")


def normalize_skills(skills):
    """Seragamkan nama skill pengguna."""
    return {
        str(skill).strip().lower()
        for skill in skills
        if skill and str(skill).strip()
    }


def skill_match(user_skills, role_skills):
    """
    Kira jumlah importance skill yang pengguna miliki
    dibahagi jumlah importance semua skill role.
    """
    total = sum(role_skills.values())

    if total <= 0:
        return 0.0

    user = normalize_skills(user_skills)

    matched = sum(
        importance
        for skill, importance in role_skills.items()
        if skill in user
    )

    return matched / total


def _get_trend_value(trends, skill, scenario):
    """Dapatkan skor scenario dalam skala 0-1."""
    info = trends.get(skill, {})
    value = info.get(scenario, DEFAULT_TREND)

    try:
        value = float(value)
    except (TypeError, ValueError):
        return DEFAULT_TREND

    # Lindungi pengiraan jika ada data luar julat.
    if not 0.0 <= value <= 1.0:
        return DEFAULT_TREND

    return value


def trend_score(role_skills, trends, scenario):
    """
    Purata skor scenario yang ditimbang mengikut importance skill.
    Skor datang daripada scenario_toggle.csv melalui data_loader.
    """
    if scenario not in SCENARIOS:
        raise ValueError(
            f"scenario mesti salah satu daripada {SCENARIOS}"
        )

    total = sum(role_skills.values())

    if total <= 0:
        return DEFAULT_TREND

    weighted = sum(
        importance * _get_trend_value(trends, skill, scenario)
        for skill, importance in role_skills.items()
    )

    return weighted / total


def score_role(user_skills, role, trends, scenario="moderate"):
    """Kira skor keseluruhan untuk satu role."""
    if scenario not in SCENARIOS:
        raise ValueError(
            f"scenario mesti salah satu daripada {SCENARIOS}"
        )

    skill_score = skill_match(user_skills, role["skills"])
    future_score = trend_score(role["skills"], trends, scenario)

    final_score = (
        W_SKILL * skill_score
        + W_TREND * future_score
    )

    return {
        "role_id": role["role_id"],
        "role_name": role["role_name"],
        "role_type": role.get("role_type", ""),
        "score": round(final_score, 4),
        "skill_match": round(skill_score, 4),
        "trend": round(future_score, 4),
        "source_url": role.get("source_url", ""),
    }


def top_roles(
    user_skills,
    roles,
    trends,
    scenario="moderate",
    n=3
):
    """Pulangkan role dengan skor tertinggi."""
    if scenario not in SCENARIOS:
        raise ValueError(
            f"scenario mesti salah satu daripada {SCENARIOS}"
        )

    scored = [
        score_role(user_skills, role, trends, scenario)
        for role in roles
    ]

    scored.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored[:n]


def skill_gap(user_skills, role):
    """Senaraikan skill role yang belum dimiliki pengguna."""
    user = normalize_skills(user_skills)

    ordered_skills = sorted(
        role["skills"].items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        skill
        for skill, _ in ordered_skills
        if skill not in user
    ]


def pathway(
    gap,
    courses,
    trends,
    scenario="moderate",
    role_skills=None
):
    """
    Susun skill yang perlu dipelajari berdasarkan
    importance dan skor scenario.
    """
    if scenario not in SCENARIOS:
        raise ValueError(
            f"scenario mesti salah satu daripada {SCENARIOS}"
        )

    role_skills = role_skills or {}

    def priority(skill):
        importance = role_skills.get(skill, 50) / 100.0
        future_score = _get_trend_value(
            trends, skill, scenario
        )

        return importance * future_score

    ordered_gap = sorted(
        gap,
        key=priority,
        reverse=True
    )

    steps = []

    for index, skill in enumerate(ordered_gap, start=1):
        trend_info = trends.get(skill, {})

        steps.append({
            "step": index,
            "skill": skill,
            "importance": role_skills.get(skill),
            "courses": courses.get(skill, []),
            "trend_source": trend_info.get("source"),
            "trend_label": trend_info.get("trend_label", ""),
            "scenario_source": trend_info.get("scenario_source", ""),
        })

    return steps
