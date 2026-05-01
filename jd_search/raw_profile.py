from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCATIONS = ["Sydney NSW", "Remote Australia"]
DEFAULT_COUNTRY = "Australia"
DEFAULT_AVOID_KEYWORDS = [
    "manager",
    "principal",
    "staff",
    "staff engineer",
    "lead engineer",
    "director",
    "sales",
    "unpaid",
    "security clearance",
]

SKILL_PATTERNS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "React": [r"\breact\b", r"\breact\.js\b"],
    "Node.js": [r"\bnode\.?js\b", r"\bnode\b"],
    "SQL": [r"\bsql\b", r"\bpostgres\b", r"\bpostgresql\b", r"\bmysql\b"],
    "AWS": [r"\baws\b", r"\bec2\b", r"\bs3\b", r"\blambda\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "LLM evaluation": [r"\bllm\b", r"language model", r"\bevaluation\b"],
    "RAG": [r"\brag\b", r"retrieval[- ]augmented"],
    "Prompt engineering": [r"\bprompt"],
    "Machine learning": [r"machine learning", r"\bml\b"],
    "PyTorch": [r"\bpytorch\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "scikit-learn": [r"\bscikit\b", r"sklearn"],
    "Data analysis": [r"data analysis", r"\banalytics\b", r"\banalyst\b"],
    "Data pipeline": [r"data pipeline", r"\betl\b", r"\bpipeline\b"],
    "API development": [r"\bapi\b", r"\brest\b", r"\bgraphql\b"],
    "Flask": [r"\bflask\b"],
    "Django": [r"\bdjango\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Testing": [r"\bpytest\b", r"\bjest\b", r"\bcypress\b", r"\btesting\b"],
    "Automation": [r"\bautomation\b", r"\bautomated\b"],
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"power bi", r"\bpowerbi\b"],
}

ROLE_RULES: dict[str, list[str]] = {
    "AI Engineer": [
        r"\bai\b",
        r"\bllm\b",
        r"language model",
        r"\brag\b",
        r"\bprompt",
        r"model evaluation",
    ],
    "Machine Learning Engineer": [
        r"machine learning",
        r"\bml\b",
        r"\bpytorch\b",
        r"\btensorflow\b",
        r"\bmodel\b",
    ],
    "Software Engineer": [
        r"software",
        r"\bpython\b",
        r"\bjavascript\b",
        r"\btypescript\b",
        r"\bapi\b",
        r"\bnode",
    ],
    "Frontend Engineer": [
        r"\breact\b",
        r"front[- ]end",
        r"\bui\b",
        r"\btypescript\b",
    ],
    "Full Stack Engineer": [
        r"full[- ]stack",
        r"\breact\b",
        r"\bnode",
        r"\bapi\b",
        r"\bdatabase\b",
    ],
    "Data Engineer": [
        r"data pipeline",
        r"\betl\b",
        r"\bsql\b",
        r"\bdatabase\b",
        r"\bpipeline\b",
    ],
    "Data Analyst": [
        r"data analysis",
        r"\banalyst\b",
        r"\banalytics\b",
        r"\bdashboard\b",
        r"\btableau\b",
        r"power bi",
    ],
    "Automation Engineer": [
        r"\bautomation\b",
        r"\bautomated\b",
        r"\btesting\b",
        r"\bworkflow\b",
    ],
}

EVIDENCE_PATTERNS: dict[str, list[str]] = {
    "AI": [r"\bai\b", r"\bllm\b", r"language model"],
    "automation": [r"\bautomation\b", r"\bautomated\b"],
    "software prototype": [r"\bprototype\b", r"web application", r"\bapi\b"],
    "data pipeline": [r"data pipeline", r"\betl\b", r"\bpipeline\b"],
    "dashboard": [r"\bdashboard\b", r"\bvisuali[sz]ation\b"],
    "evaluation": [r"\bevaluation\b", r"\btesting\b", r"\bbenchmark"],
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def count_patterns(text: str, patterns: list[str]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.I)) for pattern in patterns)


def read_pdf_text(path: Path, notes: list[str]) -> str:
    if not shutil.which("pdftotext"):
        notes.append(f"Skipped PDF text extraction for {rel(path)}: pdftotext not installed.")
        return ""
    try:
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        notes.append(f"Skipped PDF text extraction for {rel(path)}: {exc}.")
        return ""
    return result.stdout


def read_raw_documents(raw_root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    sources: list[dict[str, Any]] = []
    chunks: list[str] = []
    if not raw_root.exists():
        return "", sources, [f"Raw root does not exist: {rel(raw_root)}"]

    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.name.startswith(".") or path.name == "_TEMPLATE.md":
            continue
        text = ""
        if path.suffix.lower() in {".md", ".txt", ".tex"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif path.suffix.lower() == ".pdf":
            text = read_pdf_text(path, notes)
        else:
            notes.append(f"Skipped unsupported raw file type: {rel(path)}")
            continue

        text = text.strip()
        if not text:
            continue
        chunks.append(text)
        sources.append({"path": rel(path), "chars": len(text)})

    return "\n\n".join(chunks), sources, notes


def infer_skills(text: str) -> tuple[list[str], list[str]]:
    counted = [
        (skill, count_patterns(text, patterns))
        for skill, patterns in SKILL_PATTERNS.items()
    ]
    counted = [(skill, count) for skill, count in counted if count > 0]
    counted.sort(key=lambda item: (-item[1], item[0].lower()))
    strong = [skill for skill, count in counted if count >= 2][:12]
    usable = [skill for skill, count in counted if count == 1][:12]
    return strong, usable


def infer_roles(text: str) -> list[str]:
    scores = [
        (role, count_patterns(text, patterns))
        for role, patterns in ROLE_RULES.items()
    ]
    scores = [(role, score) for role, score in scores if score > 0]
    scores.sort(key=lambda item: (-item[1], item[0].lower()))
    roles = [role for role, _score in scores[:5]]
    return roles or ["Software Engineer"]


def infer_evidence_keywords(text: str) -> list[str]:
    hits = [
        (term, count_patterns(text, patterns))
        for term, patterns in EVIDENCE_PATTERNS.items()
    ]
    hits = [(term, count) for term, count in hits if count > 0]
    hits.sort(key=lambda item: (-item[1], item[0].lower()))
    return [term for term, _count in hits[:8]]


def build_profile_from_raw(
    raw_root: Path,
    locations: list[str] | None = None,
    country_indeed: str | None = None,
) -> dict[str, Any]:
    text, sources, notes = read_raw_documents(raw_root)
    if not text.strip():
        notes.append("No usable raw text found; using fallback Software Engineer profile.")

    strong, usable = infer_skills(text)
    roles = infer_roles(text)
    evidence = infer_evidence_keywords(text)
    return {
        "profile_name": "generated-from-raw",
        "profile_source": "raw",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "raw_root": rel(raw_root) if raw_root.is_relative_to(ROOT) else str(raw_root),
        "raw_source_count": len(sources),
        "raw_sources": sources,
        "target_roles": roles,
        "locations": locations or DEFAULT_LOCATIONS,
        "country_indeed": country_indeed or DEFAULT_COUNTRY,
        "skills": {
            "strong": strong,
            "usable": usable,
            "gap": [],
        },
        "constraints": {
            "remote_ok": True,
            "avoid_keywords": DEFAULT_AVOID_KEYWORDS,
            "required_keywords": [],
        },
        "evidence_keywords": evidence,
        "notes": notes,
    }
