"""Logik skor. Formula (setuju dengan pasukan):
    skor_role = 0.6 * skill_match + 0.4 * trend
    skill_match = skill pengguna yang padan / skill diperlukan role
    trend       = purata skor trend (0 hingga 1) bagi skill role itu
Scenario: "moderate" (AI sederhana) atau "fast" (AI laju)."""

W_SKILL = 0.6
W_TREND = 0.4
DEFAULT_TREND = 0.5  # dipakai jika skill tiada dalam trends.csv
SCENARIOS = ("moderate", "fast")


def normalize_skills(skills):
    return {s.strip().lower() for s in skills if s and s.strip()}


def skill_match(user_skills, role_skills):
    if not role_skills:
        return 0.0
    user = normalize_skills(user_skills)
    return len(user & set(role_skills)) / len(role_skills)


def trend_score(role_skills, trends, scenario):
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario mesti salah satu daripada {SCENARIOS}")
    if not role_skills:
        return DEFAULT_TREND
    vals = [trends[s][scenario] if s in trends else DEFAULT_TREND for s in role_skills]
    return sum(vals) / len(vals)


def score_role(user_skills, role, trends, scenario):
    sm = skill_match(user_skills, role["skills"])
    tr = trend_score(role["skills"], trends, scenario)
    return {
        "role_id": role["role_id"],
        "role_name": role["role_name"],
        "score": round(W_SKILL * sm + W_TREND * tr, 4),
        "skill_match": round(sm, 4),
        "trend": round(tr, 4),
        "source_url": role["source_url"],
    }


def top_roles(user_skills, roles, trends, scenario="moderate", n=3):
    scored = [score_role(user_skills, r, trends, scenario) for r in roles]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n]


def skill_gap(user_skills, role):
    user = normalize_skills(user_skills)
    return [s for s in role["skills"] if s not in user]


def pathway(gap, courses, trends, scenario="moderate"):
    """Susun skill gap: skill paling tinggi trend dipelajari dahulu."""
    ordered = sorted(
        gap,
        key=lambda s: trends[s][scenario] if s in trends else DEFAULT_TREND,
        reverse=True,
    )
    steps = []
    for i, skill in enumerate(ordered, start=1):
        steps.append({
            "step": i,
            "skill": skill,
            "courses": courses.get(skill, []),
            "trend_source": trends[skill]["source"] if skill in trends else None,
        })
    return steps
