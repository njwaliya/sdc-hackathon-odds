"""Semak data M1 dan M2 sebelum/selepas Pull.   Jalankan:  python src/check_data.py
RALAT   = mesti dibetulkan (kod akan salah padan atau rosak)
AMARAN  = patut disemak, tapi tak merosakkan kod"""
import csv
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
COLS = {
    "roles.csv": ["role_id", "role_name", "role_type", "skill_name", "skill_type",
                  "importance", "related_roles", "source_url"],
    "trends.csv": ["skill", "score_moderate", "score_fast", "source", "date"],
    "courses.csv": ["skill", "course_name", "provider", "hours", "cost", "url"],
    "sdg_map.csv": ["item_type", "item_name", "sdg_number", "reason"],
}
errors, warnings = [], []


def norm(s):
    return (s or "").strip().lower()


def load(name):
    path = DATA / name
    if not path.exists():
        errors.append(f"{name}: fail tak jumpa dalam data/")
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLS[name] if c not in (reader.fieldnames or [])]
        if missing:
            errors.append(f"{name}: lajur tiada atau salah nama: {missing}")
            return []
        return list(reader)


def number(value, lo, hi):
    try:
        return lo <= float(value) <= hi
    except (TypeError, ValueError):
        return False


roles, trends, courses, sdg = (load(n) for n in ("roles.csv", "trends.csv", "courses.csv", "sdg_map.csv"))

# ---- roles.csv
role_ids, role_names, seen = set(), {}, set()
role_skills = {}
for i, r in enumerate(roles, start=2):
    rid, sk = r["role_id"].strip(), norm(r["skill_name"])
    role_ids.add(rid)
    role_names[rid] = r["role_name"].strip()
    if not re.fullmatch(r"\d{2}-\d{4}\.\d{2}", rid):
        errors.append(f"roles.csv baris {i}: role_id '{rid}' bukan format O*NET (contoh 43-3051.00)")
    if norm(r["role_type"]) not in ("current", "future"):
        errors.append(f"roles.csv baris {i}: role_type mesti 'current' atau 'future', dapat '{r['role_type']}'")
    if not number(r["importance"], 0, 100):
        errors.append(f"roles.csv baris {i}: importance mesti nombor 0-100, dapat '{r['importance']}'")
    if not sk:
        errors.append(f"roles.csv baris {i}: skill_name kosong")
    if (rid, sk) in seen:
        errors.append(f"roles.csv baris {i}: skill '{sk}' diulang untuk role {rid}")
    seen.add((rid, sk))
    if not r["source_url"].strip():
        errors.append(f"roles.csv baris {i}: source_url kosong")
    role_skills.setdefault(sk, set()).add(rid)

types = {norm(r["role_type"]) for r in roles}
if roles and "current" not in types:
    warnings.append("roles.csv: tiada role 'current' (role asal)")
if roles and not (8 <= len(role_ids) <= 10):
    warnings.append(f"roles.csv: ada {len(role_ids)} role (checklist minta 8-10)")
for r in roles:
    for code in [c.strip() for c in r["related_roles"].split(";") if c.strip()]:
        if code not in role_ids:
            warnings.append(f"roles.csv: related_roles '{code}' (role {r['role_id'].strip()}) tiada dalam roles.csv")
warnings = list(dict.fromkeys(warnings))

# ---- trends.csv
trend_skills = {}
for i, r in enumerate(trends, start=2):
    sk = norm(r["skill"])
    trend_skills[sk] = r
    for col in ("score_moderate", "score_fast"):
        if not number(r[col], 0, 1):
            errors.append(f"trends.csv baris {i}: {col} mesti nombor 0-1, dapat '{r[col]}'")
    if not r["source"].strip() or not r["date"].strip():
        errors.append(f"trends.csv baris {i}: source atau date kosong")

# ---- courses.csv
course_skills = set()
for i, r in enumerate(courses, start=2):
    course_skills.add(norm(r["skill"]))
    if not r["url"].strip():
        errors.append(f"courses.csv baris {i}: url kosong")

# ---- padanan nama skill
for sk in sorted(set(role_skills) - set(trend_skills)):
    errors.append(f"SKILL TAK PADAN: '{sk}' ada dalam roles.csv tapi tiada dalam trends.csv (M2)")
for sk in sorted(set(trend_skills) - set(role_skills)):
    warnings.append(f"trends.csv: '{sk}' tiada dalam roles.csv (tak akan digunakan, semak ejaan)")
for sk in sorted(course_skills - set(role_skills)):
    warnings.append(f"courses.csv: '{sk}' tiada dalam roles.csv (tak akan digunakan, semak ejaan)")
for sk in sorted(set(role_skills) - course_skills):
    warnings.append(f"courses.csv: tiada kursus untuk skill '{sk}'")

# ---- sdg
tagged = {norm(r["item_name"]) for r in sdg if norm(r["item_type"]) == "role"}
for rid, name in role_names.items():
    if norm(name) not in tagged:
        warnings.append(f"sdg_map.csv: role '{name}' belum ada tag SDG")
for i, r in enumerate(sdg, start=2):
    if not number(r["sdg_number"], 1, 17):
        errors.append(f"sdg_map.csv baris {i}: sdg_number mesti 1-17, dapat '{r['sdg_number']}'")

# ---- placeholder SAMPLE
for name in COLS:
    p = DATA / name
    if p.exists():
        n = p.read_text(encoding="utf-8-sig").count("SAMPLE")
        if n:
            warnings.append(f"{name}: masih ada {n} baris/nilai bertulis 'SAMPLE' (data contoh)")

print(f"Role: {len(role_ids)} | Skill unik: {len(role_skills)} | Trend: {len(trend_skills)} | "
      f"Skill ada kursus: {len(course_skills & set(role_skills))}")
print(f"\nRALAT ({len(errors)})")
for e in errors:
    print("  X", e)
print(f"\nAMARAN ({len(warnings)})")
for w in warnings:
    print("  !", w)
print("\nSEMUA OK" if not errors and not warnings else
      "\nBetulkan RALAT dahulu." if errors else "\nTiada ralat. Semak AMARAN.")
sys.exit(1 if errors else 0)
