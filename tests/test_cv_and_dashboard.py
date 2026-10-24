import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import app as backend
import cv_skills


def make_docx(text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f"<w:document><w:body><w:p><w:t>{text}</w:t></w:p></w:body></w:document>")
    return buf.getvalue()


def test_detect_skills_scores_by_distinct_keywords():
    res = cv_skills.detect_skills("Processed payroll, EPF and SOCSO calculation; prepared reports.", {"economics and accounting", "personnel and human resources", "mathematics"})
    by = {r["name"]: r for r in res}
    assert by["economics and accounting"]["score"] == 60      # 2 kata kunci: epf, socso
    assert by["economics and accounting"]["level"] == "Moderate"
    assert by["mathematics"]["level"] == "Basic mention"      # 1 kata kunci: calculation


def test_upload_cv_docx_returns_skills_and_scores():
    c = backend.app.test_client()
    data = {"cv_file": (io.BytesIO(make_docx("Payroll officer. Managed EPF SOCSO contributions, Excel calculation, report writing, met deadlines.")), "cv.docx")}
    r = c.post("/api/upload-cv", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    j = r.get_json()
    assert j["skills"] and j["skill_scores"][0]["score"] >= j["skill_scores"][-1]["score"]


def test_upload_cv_rejects_bad_files():
    c = backend.app.test_client()
    for name, payload in [("cv.txt", b"hello world hello world hello"), ("cv.pdf", b"not a pdf at all, really not")]:
        r = c.post("/api/upload-cv", data={"cv_file": (io.BytesIO(payload), name)}, content_type="multipart/form-data")
        assert r.status_code == 400 and "error" in r.get_json()
    assert c.post("/api/upload-cv").status_code == 400


def test_dashboard_trends_shape_and_validation():
    c = backend.app.test_client()
    for scn in ("moderate", "fast"):
        j = c.get(f"/api/dashboard-trends?scenario={scn}").get_json()
        assert {"rising", "declining", "all_skills", "resilient", "total_skills"} <= set(j)
        assert all(0 <= i["score"] <= 100 for i in j["all_skills"])
    assert c.get("/api/dashboard-trends?scenario=bad").status_code == 400


def test_pages_are_served():
    c = backend.app.test_client()
    assert c.get("/").status_code == 200
    assert c.get("/dashboard.html").status_code == 200
