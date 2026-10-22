
"""Membaca data CSV untuk sistem SDC Hackathon."""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DEFAULT_TREND = 0.5


def _norm(text):
    """Tukar teks kepada huruf kecil dan buang ruang kosong."""
    return (text or "").strip().lower()


def _read(filename, data_dir=None):
    """Baca CSV menggunakan UTF-8 dan pulangkan senarai dictionary."""
    folder = Path(data_dir) if data_dir is not None else DATA_DIR
    path = folder / filename

    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def _number_or_default(value, default=DEFAULT_TREND):
    """Tukar skor 1-10 kepada 0-1. N/A atau kosong menggunakan fallback."""
    value = (value or "").strip()

    if not value or value.upper() in {"N/A", "NA", "NONE"}:
        return default

    try:
        score = float(value)
    except ValueError:
        return default

    # Skor scenario dalam CSV sepatutnya berada pada skala 1 hingga 10.
    if not 1 <= score <= 10:
        return default

    return score / 10.0


def load_roles(data_dir=None):
    """
    roles.csv:
    role_id, role_name, role_type, skill_name, skill_type,
    importance, related_roles, source_url
    """
    roles = {}

    for row in _read("roles.csv", data_dir):
        role_id = (row.get("role_id") or "").strip()
        skill_name = _norm(row.get("skill_name"))

        if not role_id or not skill_name:
            continue

        if role_id not in roles:
            related = (row.get("related_roles") or "").split(";")

            roles[role_id] = {
                "role_id": role_id,
                "role_name": (row.get("role_name") or "").strip(),
                "role_type": _norm(row.get("role_type")),
                "related_roles": [
                    item.strip() for item in related if item.strip()
                ],
                "source_url": (row.get("source_url") or "").strip(),
                "skills": {},
                "skill_types": {},
            }

        try:
            importance = float(row.get("importance") or 0)
        except ValueError:
            importance = 0.0

        roles[role_id]["skills"][skill_name] = importance
        roles[role_id]["skill_types"][skill_name] = _norm(
            row.get("skill_type")
        )

    return list(roles.values())



def load_trends(data_dir=None):
    trends = {}

    # 1. Baca label trend daripada trends.csv
    for r in _read("trends.csv", data_dir):
        skill = _norm(r.get("skill_name") or r.get("skill") or "")

        if not skill:
            continue

        trends[skill] = {
            "moderate": DEFAULT_TREND,
            "fast": DEFAULT_TREND,
            "trend_label": _norm(r.get("trend") or ""),
            "source": (r.get("source") or "").strip(),
            "source_url": (r.get("source_url") or "").strip(),
            "date": (
                r.get("source_date") or r.get("date") or ""
            ).strip(),
        }

    # 2. Baca skor senario daripada scenario_toggle.csv
    for r in _read("scenario_toggle.csv", data_dir):
        skill = _norm(r.get("skill_name") or r.get("skill") or "")

        if not skill:
            continue

        if skill not in trends:
            trends[skill] = {
                "moderate": DEFAULT_TREND,
                "fast": DEFAULT_TREND,
                "trend_label": "",
                "source": "",
                "source_url": "",
                "date": "",
            }

        for column, scenario in [
            ("moderate_ai", "moderate"),
            ("fast_ai", "fast"),
        ]:
            value = (r.get(column) or "").strip()

            if not value or value.upper() == "N/A":
                trends[skill][scenario] = DEFAULT_TREND
            else:
                score = float(value)

                if not 1 <= score <= 10:
                    raise ValueError(
                        f"Skor {column} untuk '{skill}' "
                        f"mesti antara 1 hingga 10."
                    )

                trends[skill][scenario] = score / 10

        trends[skill]["scenario_source"] = (
            r.get("source") or ""
        ).strip()
        trends[skill]["scenario_date"] = (
            r.get("source_date") or ""
        ).strip()
        trends[skill]["score_note"] = (
            r.get("score_note") or ""
        ).strip()

    return trends


def load_scenario_toggle(data_dir=None):
    """
    Pulangkan skor scenario secara berasingan jika diperlukan oleh UI.
    Skor yang dipulangkan berada pada skala 0-1.
    """
    scenarios = {}

    for row in _read("scenario_toggle.csv", data_dir):
        skill = _norm(row.get("skill_name"))

        if not skill:
            continue

        scenarios[skill] = {
            "moderate": _number_or_default(row.get("moderate_ai")),
            "fast": _number_or_default(row.get("fast_ai")),
            "source": (row.get("source") or "").strip(),
            "date": (row.get("source_date") or "").strip(),
            "score_note": (row.get("score_note") or "").strip(),
        }

    return scenarios


def load_courses(data_dir=None):
    """
    courses.csv:
    skill_name, course_name, provider, duration,
    cost_status, date_checked, url

    Kekalkan keys 'hours' dan 'cost' untuk keserasian dengan
    kod UI lama jika kod tersebut masih menggunakannya.
    """
    courses = {}

    for row in _read("courses.csv", data_dir):
        skill = _norm(row.get("skill_name"))

        if not skill:
            continue

        duration = (row.get("duration") or "").strip()
        cost_status = (row.get("cost_status") or "").strip()

        course = {
            "course_name": (row.get("course_name") or "").strip(),
            "provider": (row.get("provider") or "").strip(),
            "duration": duration,
            "cost_status": cost_status,
            "date_checked": (row.get("date_checked") or "").strip(),
            "url": (row.get("url") or "").strip(),

            # Alias untuk kod lama.
            "hours": duration,
            "cost": cost_status,
        }

        courses.setdefault(skill, []).append(course)

    return courses


def load_sdg(data_dir=None):
    """
    sdg_map.csv:
    item_type, item_name, sdg_number, sdg_target, reason, source
    """
    sdg = {}

    for row in _read("sdg_map.csv", data_dir):
        item_type = _norm(row.get("item_type"))
        item_name = _norm(row.get("item_name"))

        if not item_type or not item_name:
            continue

        # Abaikan contoh sementara yang belum diganti oleh pasukan.
        if "sample" in item_name or "sample" in _norm(row.get("reason")):
            continue

        item = {
            "sdg_number": (row.get("sdg_number") or "").strip(),
            "sdg_target": (row.get("sdg_target") or "").strip(),
            "reason": (row.get("reason") or "").strip(),
            "source": (row.get("source") or "").strip(),
        }

        sdg.setdefault((item_type, item_name), []).append(item)

    return sdg
