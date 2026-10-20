"""API backend (Flask). Frontend M4 panggil POST /api/match.
Jalankan:  python src/app.py"""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

import data_loader as dl
import scoring as sc

app = Flask(__name__)
CORS(app)


def get_data():
    # Dibaca setiap request supaya perubahan CSV terus nampak tanpa restart.
    return dl.load_roles(), dl.load_trends(), dl.load_courses(), dl.load_sdg()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/match")
def match():
    body = request.get_json(silent=True) or {}
    skills = body.get("skills", [])
    scenario = body.get("scenario", "moderate")
    if not isinstance(skills, list) or not skills:
        return jsonify({"error": "Sila hantar 'skills' sebagai senarai yang tidak kosong."}), 400
    if scenario not in sc.SCENARIOS:
        return jsonify({"error": f"'scenario' mesti salah satu: {sc.SCENARIOS}"}), 400

    roles, trends, courses, sdg = get_data()
    by_id = {r["role_id"]: r for r in roles}
    results = []
    for top in sc.top_roles(skills, roles, trends, scenario, n=3):
        role = by_id[top["role_id"]]
        gap = sc.skill_gap(skills, role)
        top["skill_gap"] = gap
        top["pathway"] = sc.pathway(gap, courses, trends, scenario)
        top["sdg"] = sdg.get(("role", role["role_name"].lower()), [])
        results.append(top)

    return jsonify({
        "scenario": scenario,
        "disclaimer": "Ramalan ialah anggaran. Keputusan akhir di tangan pengguna.",
        "results": results,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
