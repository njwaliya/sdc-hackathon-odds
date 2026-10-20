"""Baca semua data dari fail CSV dalam folder data/.
Data TIDAK ditaip dalam kod. M1 dan M2 hanya perlu kemas kini fail CSV."""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _norm(text):
    return text.strip().lower()


def _split(value):
    """'a; b ;c' -> ['a', 'b', 'c'] (huruf kecil)."""
    return [_norm(v) for v in (value or "").split(";") if v.strip()]


def _read(filename, data_dir=None):
    path = Path(data_dir or DATA_DIR) / filename
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_roles(data_dir=None):
    roles = []
    for r in _read("roles.csv", data_dir):
        roles.append({
            "role_id": r["role_id"].strip(),
            "role_name": r["role_name"].strip(),
            "skills": _split(r["skills"]),
            "related_roles": [x.strip() for x in r["related_roles"].split(";") if x.strip()],
            "source_url": r["source_url"].strip(),
        })
    return roles


def load_trends(data_dir=None):
    trends = {}
    for r in _read("trends.csv", data_dir):
        trends[_norm(r["skill"])] = {
            "moderate": float(r["score_moderate"]),
            "fast": float(r["score_fast"]),
            "source": r["source"].strip(),
            "date": r["date"].strip(),
        }
    return trends


def load_courses(data_dir=None):
    courses = {}
    for r in _read("courses.csv", data_dir):
        courses.setdefault(_norm(r["skill"]), []).append({
            "course_name": r["course_name"].strip(),
            "provider": r["provider"].strip(),
            "hours": r["hours"].strip(),
            "cost": r["cost"].strip(),
            "url": r["url"].strip(),
        })
    return courses


def load_sdg(data_dir=None):
    sdg = {}
    for r in _read("sdg_map.csv", data_dir):
        sdg.setdefault((_norm(r["item_type"]), _norm(r["item_name"])), []).append({
            "sdg_number": r["sdg_number"].strip(),
            "reason": r["reason"].strip(),
        })
    return sdg
