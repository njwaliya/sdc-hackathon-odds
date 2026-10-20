import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import data_loader as dl
import scoring as sc


def test_skill_match_full_and_partial():
    assert sc.skill_match(["Excel", "communication"], ["excel", "communication"]) == 1.0
    assert sc.skill_match(["excel"], ["excel", "communication"]) == 0.5
    assert sc.skill_match([], ["excel"]) == 0.0


def test_top3_returns_three_sorted():
    roles, trends = dl.load_roles(), dl.load_trends()
    res = sc.top_roles(["excel", "communication"], roles, trends, "moderate")
    assert len(res) == 3
    assert res[0]["score"] >= res[1]["score"] >= res[2]["score"]


def test_scenario_changes_ranking_score():
    roles, trends = dl.load_roles(), dl.load_trends()
    a = sc.top_roles(["payroll processing"], roles, trends, "moderate")[0]["score"]
    b = sc.top_roles(["payroll processing"], roles, trends, "fast")[0]["score"]
    assert a != b


def test_skill_gap_and_pathway():
    roles, trends, courses = dl.load_roles(), dl.load_trends(), dl.load_courses()
    role = roles[0]
    gap = sc.skill_gap(["excel"], role)
    assert "excel" not in gap
    steps = sc.pathway(gap, courses, trends, "moderate")
    assert [s["step"] for s in steps] == list(range(1, len(gap) + 1))
