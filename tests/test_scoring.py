"""Ujian guna data tetap dalam tests/fixtures/, bukan data/ sebenar,
supaya ujian tak gagal bila M1 dan M2 tukar data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import data_loader as dl
import scoring as sc

FIX = Path(__file__).resolve().parent / "fixtures"


def test_skill_match_is_weighted_by_importance():
    role = {"excel": 75, "communication": 25}
    assert sc.skill_match(["Excel", "communication"], role) == 1.0
    assert sc.skill_match(["excel"], role) == 0.75
    assert sc.skill_match(["communication"], role) == 0.25
    assert sc.skill_match([], role) == 0.0


def test_roles_loaded_in_long_format():
    roles = dl.load_roles(FIX)
    payroll = next(r for r in roles if r["role_id"] == "43-3051.00")
    assert payroll["role_type"] == "current"
    assert payroll["skills"]["reading comprehension"] == 72.0
    assert "43-3031.00" in payroll["related_roles"]


def test_top3_returns_three_sorted():
    roles, trends = dl.load_roles(FIX), dl.load_trends(FIX)
    res = sc.top_roles(["excel", "communication"], roles, trends, "moderate")
    assert len(res) == 3
    assert res[0]["score"] >= res[1]["score"] >= res[2]["score"]


def test_scenario_changes_score():
    roles, trends = dl.load_roles(FIX), dl.load_trends(FIX)
    a = sc.top_roles(["mathematics"], roles, trends, "moderate")[0]["score"]
    b = sc.top_roles(["mathematics"], roles, trends, "fast")[0]["score"]
    assert a != b


def test_skill_gap_sorted_by_importance_and_pathway():
    roles = dl.load_roles(FIX)
    trends = dl.load_trends(FIX)
    courses = dl.load_courses(FIX)

    role = next(
        r for r in roles
        if r["role_id"] == "13-1071.00"
    )

    gap = sc.skill_gap(["speaking"], role)

    # Skill yang sudah dikuasai tidak patut muncul dalam gap
    assert "speaking" not in gap

    # Skill gap disusun mengikut importance tertinggi
    importance_values = [
        role["skills"][skill] for skill in gap
    ]
    assert importance_values == sorted(
        importance_values, reverse=True
    )

    # Pastikan pathway mempunyai nombor langkah yang betul
    steps = sc.pathway(
        gap, courses, trends, "moderate", role["skills"]
    )
    assert [s["step"] for s in steps] == list(
        range(1, len(gap) + 1)
    )


def test_unknown_skill_in_trends_uses_default():
    role = {"mystery skill": 100}
    assert sc.trend_score(role, {}, "fast") == sc.DEFAULT_TREND
