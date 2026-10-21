"""Logik skor. Formula (setuju dengan pasukan):
    skor_role = 0.6 * skill_match + 0.4 * trend
    skill_match = jumlah importance skill yang padan / jumlah importance semua skill role
    trend       = purata trend (0 hingga 1) bagi skill role, ditimbang dengan importance
Skill yang lebih penting (importance tinggi) lebih berat dalam kedua-dua kiraan.
Scenario: "moderate" (AI sederhana) atau "fast" (AI laju)."""

W_SKILL = 0.6
W_TREND = 0.4
DEFAULT_TREND = 0.5  # dipakai jika skill tiada dalam trends.csv
SCENARIOS = ("moderate", "fast")


def normalize_skills(skills):
    return {s.strip().lower() for s in skills if s and s.strip()}


def skill_match(user_skills, role_skills):
    """role_skills: dict {skill: importance}."""
    total = sum(role_skills.values())
    if total <= 0:
        return 0.0
    user = normalize_skills(user_skills)
    return sum(w for s, w in role_skills.items() if s in user) / total


def trend_score(role_skills, trends, scenario):
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario mesti salah satu daripada {SCENARIOS}")
    total = sum(role_skills.values())
    if total <= 0:
        return DEFAULT_TREND
    weighted = sum(
        w * (trends[s][scenario] if s in trends else DEFAULT_TREND)
        for s, w in role_skills.items()
    )
    return weighted / total


def score_role(user_skills, role, trends, scenario):
    sm = skill_match(user_skills, role["skills"])
    tr = trend_score(role["skills"], trends, scenario)
    return {
        "role_id": role["role_id"],
        "role_name": role["role_name"],
        "role_type": role.get("role_type", ""),
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
    """Skill yang role perlukan tapi pengguna belum ada, paling penting dahulu."""
    user = normalize_skills(user_skills)
    items = sorted(role["skills"].items(), key=lambda kv: kv[1], reverse=True)
    return [s for s, _ in items if s not in user]


def pathway(gap, courses, trends, scenario="moderate", role_skills=None):
    """Susun skill gap: (importance x trend) tertinggi dipelajari dahulu."""
    role_skills = role_skills or {}

    def priority(skill):
        imp = role_skills.get(skill, 50) / 100
        tr = trends[skill][scenario] if skill in trends else DEFAULT_TREND
        return imp * tr

    ordered = sorted(gap, key=priority, reverse=True)
    steps = []
    for i, skill in enumerate(ordered, start=1):
        steps.append({
            "step": i,
            "skill": skill,
            "importance": role_skills.get(skill),
            "courses": courses.get(skill, []),
            "trend_source": trends[skill]["source"] if skill in trends else None,
        })
    return steps
