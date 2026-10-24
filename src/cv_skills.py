"""Baca CV (PDF/DOCX) dan anggar skill berdasarkan KATA KUNCI.

Kaedah: padanan kata kunci pada teks CV, BUKAN model AI. Setiap skill O*NET dalam
roles.csv mempunyai senarai kata kunci/frasa lazim dalam CV. Skor menunjukkan
kekuatan bukti (bilangan kata kunci berbeza yang dijumpai), bukan tahap kemahiran.
CV diproses dalam memori sahaja: tidak disimpan ke cakera, repo atau log."""
import io
import re
import zipfile

MAX_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 15

# skill (huruf kecil, sama dengan roles.csv) -> kata kunci dalam CV (padanan awalan)
KEYWORDS = {
    "active learning": ["upskill", "self-learning", "self-taught", "certification", "certified", "professional development", "continuous learning"],
    "active listening": ["active listening", "listening", "client needs", "stakeholder feedback", "employee feedback"],
    "administration and management": ["administration", "office management", "operations management", "managed office", "office administration"],
    "administrative": ["administrative", "admin ", "filing", "data entry", "clerical", "document management", "records"],
    "complex problem solving": ["problem solving", "problem-solving", "troubleshoot", "root cause", "resolved issues", "issue resolution"],
    "computers and electronics": ["microsoft office", "excel", "spreadsheet", "software", "sap ", "erp", "hris", "database", "payroll system"],
    "coordination": ["coordinat", "liaise", "liaising", "cross-functional", "collaborat"],
    "critical thinking": ["critical thinking", "analytical", "analysis", "analyse", "analyze", "evaluate"],
    "customer and personal service": ["customer service", "client service", "customer support", "employee queries", "helpdesk", "front desk", "client relations"],
    "economics and accounting": ["accounting", "bookkeeping", "accounts payable", "accounts receivable", "ledger", "reconciliation", "financial reporting", "epf", "socso", "eis", "pcb"],
    "education and training": ["training", "trained", "mentor", "onboarding", "coaching", "teaching"],
    "english language": ["english", "bilingual", "fluent", "muet", "ielts", "toefl"],
    "instructing": ["instruct", "taught", "workshop", "briefing", "mentoring"],
    "judgment and decision making": ["decision", "judgment", "judgement", "prioritis", "prioritiz", "approval"],
    "law and government": ["employment law", "labour law", "labor law", "compliance", "statutory", "regulation", "legislation", "employment act"],
    "learning strategies": ["learning strategy", "training plan", "learning plan", "curriculum", "training programme", "training program"],
    "management of financial resources": ["budget", "cost control", "financial management", "expense", "forecast", "cash flow"],
    "management of personnel resources": ["supervis", "team lead", "managed team", "led a team", "staff management", "manage staff", "attendance", "timekeeping"],
    "mathematics": ["calculation", "calculate", "numeracy", "mathematics", "statistics", "accuracy", "percentage", "formula"],
    "mathematics (knowledge)": ["calculation", "calculate", "numeracy", "mathematics", "statistics", "accuracy", "percentage", "formula"],
    "monitoring": ["monitor", "tracking", "oversee", "quality check", "verify", "verification", "audit"],
    "negotiation": ["negotiat", "contract terms", "vendor terms", "settlement"],
    "personnel and human resources": ["human resources", "hr ", "payroll", "recruitment", "employee benefits", "leave management", "employee records"],
    "persuasion": ["persuad", "influence", "convince", "pitch", "advocate"],
    "public safety and security": ["safety", "security", "confidential", "data protection", "pdpa", "osha", "privacy", "risk management"],
    "reading comprehension": ["document review", "reviewing documents", "interpret", "policy documents", "reports", "documentation"],
    "sales and marketing": ["sales", "marketing", "promotion", "business development", "campaign"],
    "service orientation": ["service oriented", "customer-focused", "customer focus", "employee support", "support staff", "assist"],
    "social perceptiveness": ["empathy", "interpersonal", "emotional intelligence", "teamwork", "team player", "people skills"],
    "speaking": ["presentation", "presenting", "public speaking", "communicat", "verbal"],
    "systems analysis": ["systems analysis", "process analysis", "process improvement", "workflow", "process mapping", "automation"],
    "systems evaluation": ["system evaluation", "system testing", "uat", "quality assurance", "testing"],
    "time management": ["deadline", "time management", "multitask", "punctual", "on time", "schedule"],
    "writing": ["report writing", "written", "writing", "drafting", "correspondence", "memo", "minutes", "wrote"],
}


class CVError(ValueError):
    """Ralat yang selamat dipaparkan kepada pengguna."""


def extract_text(filename, data):
    name = (filename or "").lower()
    if len(data) > MAX_BYTES:
        raise CVError("Fail terlalu besar (maksimum 5 MB).")
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF"):
            raise CVError("Fail bukan PDF yang sah.")
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in reader.pages[:MAX_PDF_PAGES])
        except Exception:
            raise CVError("PDF tidak dapat dibaca (mungkin dilindungi kata laluan).")
    if name.endswith(".docx"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
        except Exception:
            raise CVError("Fail DOCX tidak sah.")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", " ", xml)
    raise CVError("Hanya fail PDF atau DOCX diterima.")


def _level(hits):
    return "Strong" if hits >= 3 else "Moderate" if hits == 2 else "Basic mention"


def _score(hits):
    return {1: 40, 2: 60, 3: 75}.get(hits, 90)


def detect_skills(text, known_skills=None):
    """Pulangkan senarai {name, score, level, evidence} disusun mengikut skor.
    known_skills: hadkan kepada skill yang ada dalam roles.csv."""
    low = " " + re.sub(r"\s+", " ", (text or "").lower()) + " "
    results = []
    for skill, words in KEYWORDS.items():
        if known_skills is not None and skill not in known_skills:
            continue
        found = [w.strip() for w in words if re.search(r"(?<![a-z])" + re.escape(w), low)]
        if found:
            results.append({"name": skill, "score": _score(len(found)),
                            "level": _level(len(found)), "evidence": [f"keyword: {w}" for w in found[:4]]})
    results.sort(key=lambda r: (-r["score"], r["name"]))
    return results
