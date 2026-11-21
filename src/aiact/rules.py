"""The legal data the assessment is built on.

Sources: Regulation (EU) 2024/1689 (the AI Act) as amended by Regulation (EU) 2026/1744
(the Digital Omnibus on AI, in force 27 July 2026). Every rule cites its article so a reviewer
can check it against the text. This is engineering support for a compliance team, not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# ---------------------------------------------------------------- application dates
PROHIBITIONS = date(2025, 2, 2)  # Art. 5, Art. 4 (Art. 113(a))
GPAI = date(2025, 8, 2)  # Chapter V, penalties (Art. 113(b))
GPAI_LEGACY = date(2027, 8, 2)  # GPAI models placed on the market before 2 Aug 2025 (Art. 111(3))
TRANSPARENCY = date(2026, 8, 2)  # Art. 50
MARKING_LEGACY = date(2026, 12, 2)  # Art. 50(2) for systems placed on the market before 2 Aug 2026 (Omnibus)
NEW_PROHIBITIONS = date(2026, 12, 2)  # non-consensual intimate imagery / CSAM generation (Omnibus)
ANNEX_III = date(2027, 12, 2)  # stand-alone high-risk systems (Omnibus; was 2 Aug 2026)
ANNEX_I = date(2028, 8, 2)  # high-risk AI in products under Annex I law (Omnibus; was 2 Aug 2027)

# ---------------------------------------------------------------- Article 5 prohibited practices
PROHIBITED_PRACTICES: dict[str, tuple[str, str, date]] = {
    "manipulation": (
        "Art. 5(1)(a)",
        "Subliminal, manipulative or deceptive techniques causing significant harm",
        PROHIBITIONS,
    ),
    "exploiting_vulnerabilities": (
        "Art. 5(1)(b)",
        "Exploiting vulnerabilities due to age, disability or social or economic situation",
        PROHIBITIONS,
    ),
    "social_scoring": ("Art. 5(1)(c)", "Social scoring leading to detrimental or unfavourable treatment", PROHIBITIONS),
    "predictive_policing": (
        "Art. 5(1)(d)",
        "Predicting criminal offences based solely on profiling or personality traits",
        PROHIBITIONS,
    ),
    "facial_scraping": (
        "Art. 5(1)(e)",
        "Untargeted scraping of facial images to build recognition databases",
        PROHIBITIONS,
    ),
    "emotion_recognition_work_education": (
        "Art. 5(1)(f)",
        "Emotion recognition in the workplace or education (except medical or safety reasons)",
        PROHIBITIONS,
    ),
    "sensitive_biometric_categorisation": (
        "Art. 5(1)(g)",
        "Biometric categorisation inferring race, political opinions, trade-union membership, religion, sex life or sexual orientation",
        PROHIBITIONS,
    ),
    "realtime_rbi_law_enforcement": (
        "Art. 5(1)(h)",
        "Real-time remote biometric identification in public spaces for law enforcement (narrow exceptions)",
        PROHIBITIONS,
    ),
    "intimate_imagery_csam": (
        "Art. 5 (Omnibus)",
        "Generating non-consensual intimate imagery or child sexual abuse material",
        NEW_PROHIBITIONS,
    ),
}

# ---------------------------------------------------------------- Annex III high-risk areas
ANNEX_III_AREAS: dict[str, str] = {
    "biometrics": "Annex III(1) Biometrics: remote identification, categorisation, emotion recognition",
    "critical_infrastructure": "Annex III(2) Safety components of critical infrastructure",
    "education": "Annex III(3) Education and vocational training: admission, assessment, proctoring",
    "employment": "Annex III(4) Employment: recruitment, selection, promotion, termination, task allocation, monitoring",
    "essential_services": "Annex III(5)(a)/(d) Eligibility for public benefits; emergency call triage",
    "credit_scoring": "Annex III(5)(b) Creditworthiness and credit scoring of natural persons",
    "insurance_pricing": "Annex III(5)(c) Risk assessment and pricing in life and health insurance",
    "law_enforcement": "Annex III(6) Law enforcement",
    "migration": "Annex III(7) Migration, asylum and border control",
    "justice_democracy": "Annex III(8) Administration of justice and democratic processes",
}

# Art. 6(3): an Annex III system is not high-risk if it poses no significant risk and only does one of these.
ART6_3_CONDITIONS: dict[str, str] = {
    "narrow_procedural": "Art. 6(3)(a) performs a narrow procedural task",
    "improve_human": "Art. 6(3)(b) improves the result of a previously completed human activity",
    "detect_patterns": "Art. 6(3)(c) detects decision-making patterns without replacing human assessment",
    "preparatory": "Art. 6(3)(d) performs a preparatory task to an assessment",
}

ROLES = ("provider", "deployer")


@dataclass(frozen=True)
class Obligation:
    id: str
    article: str
    title: str
    role: str  # provider | deployer
    applies_from: date
    evidence_hint: str


def _hr(id_: str, article: str, title: str, role: str, start: date, hint: str) -> Obligation:
    return Obligation(id_, article, title, role, start, hint)


def high_risk_obligations(start: date) -> list[Obligation]:
    """Chapter III obligations for a high-risk system; `start` is 2 Dec 2027 (Annex III) or 2 Aug 2028 (Annex I)."""
    return [
        _hr(
            "HR-RISK",
            "Art. 9",
            "Risk management system across the lifecycle",
            "provider",
            start,
            "risk register, test results",
        ),
        _hr(
            "HR-DATA",
            "Art. 10",
            "Data governance: relevance, representativeness, bias examination",
            "provider",
            start,
            "dataset sheets, bias analysis",
        ),
        _hr("HR-TECHDOC", "Art. 11, Annex IV", "Technical documentation", "provider", start, "Annex IV document"),
        _hr(
            "HR-LOGS",
            "Art. 12",
            "Automatic event logging for traceability",
            "provider",
            start,
            "logging design, retention",
        ),
        _hr(
            "HR-INSTRUCTIONS",
            "Art. 13",
            "Transparency and instructions for use for deployers",
            "provider",
            start,
            "instructions for use",
        ),
        _hr(
            "HR-OVERSIGHT",
            "Art. 14",
            "Human oversight measures designed in",
            "provider",
            start,
            "oversight design, override paths",
        ),
        _hr(
            "HR-ROBUST",
            "Art. 15",
            "Accuracy, robustness and cybersecurity",
            "provider",
            start,
            "metrics, adversarial tests",
        ),
        _hr("HR-QMS", "Art. 17", "Quality management system", "provider", start, "QMS procedures"),
        _hr(
            "HR-CONFORMITY",
            "Art. 43, 47, 48",
            "Conformity assessment, EU declaration, CE marking",
            "provider",
            start,
            "declaration of conformity",
        ),
        _hr("HR-REGISTER", "Art. 49", "Registration in the EU database", "provider", start, "registration record"),
        _hr("HR-PMM", "Art. 72", "Post-market monitoring plan", "provider", start, "monitoring plan"),
        _hr("HR-INCIDENT", "Art. 73", "Serious incident reporting procedure", "provider", start, "incident runbook"),
        _hr(
            "DEP-USE",
            "Art. 26(1)",
            "Use according to the instructions for use",
            "deployer",
            start,
            "operating procedure",
        ),
        _hr(
            "DEP-OVERSIGHT",
            "Art. 26(2)",
            "Assign competent, trained human oversight",
            "deployer",
            start,
            "named overseers, training",
        ),
        _hr(
            "DEP-INPUT", "Art. 26(4)", "Input data relevant and representative", "deployer", start, "input data checks"
        ),
        _hr(
            "DEP-MONITOR",
            "Art. 26(5)",
            "Monitor operation; inform provider and authorities of risks",
            "deployer",
            start,
            "monitoring procedure",
        ),
        _hr(
            "DEP-LOGS",
            "Art. 26(6)",
            "Keep automatically generated logs for at least six months",
            "deployer",
            start,
            "log retention config",
        ),
        _hr(
            "DEP-INFORM",
            "Art. 26(11)",
            "Inform people subject to decisions that the system is used",
            "deployer",
            start,
            "notice text",
        ),
        _hr(
            "DEP-EXPLAIN",
            "Art. 86",
            "Explain individual decisions on request",
            "deployer",
            start,
            "explanation procedure",
        ),
    ]


def workplace_obligation(start: date) -> Obligation:
    return _hr(
        "DEP-WORKERS",
        "Art. 26(7)",
        "Inform workers' representatives and affected workers before use",
        "deployer",
        start,
        "consultation record",
    )


def fria_obligation(start: date) -> Obligation:
    return _hr(
        "DEP-FRIA",
        "Art. 27",
        "Fundamental rights impact assessment before first use",
        "deployer",
        start,
        "FRIA document",
    )


def art6_3_obligations(start: date) -> list[Obligation]:
    return [
        _hr(
            "EX-DOC",
            "Art. 6(4)",
            "Document why the Annex III system is not high-risk",
            "provider",
            start,
            "Art. 6(3) assessment",
        ),
        _hr(
            "EX-REGISTER",
            "Art. 49(2)",
            "Register the system in the EU database despite the exemption",
            "provider",
            start,
            "registration record",
        ),
    ]


LITERACY = Obligation(
    "LITERACY",
    "Art. 4 (as amended)",
    "Take measures to support AI literacy of staff operating the system",
    "both",
    PROHIBITIONS,
    "training plan, attendance",
)

TRANSPARENCY_RULES: dict[str, tuple[str, str, str]] = {
    # flag -> (id, article, title); role decided per rule below
    "interacts_with_people": (
        "T-INTERACT",
        "Art. 50(1)",
        "Tell people they are interacting with an AI system (unless obvious)",
    ),
    "generates_synthetic_content": (
        "T-MARKING",
        "Art. 50(2)",
        "Mark synthetic audio, image, video or text as AI-generated in a machine-readable, detectable way",
    ),
    "emotion_recognition": (
        "T-EMOTION",
        "Art. 50(3)",
        "Inform people exposed to emotion recognition or biometric categorisation",
    ),
    "biometric_categorisation": (
        "T-EMOTION",
        "Art. 50(3)",
        "Inform people exposed to emotion recognition or biometric categorisation",
    ),
    "deepfakes": ("T-DEEPFAKE", "Art. 50(4)", "Disclose that image, audio or video content is a deep fake"),
    "public_interest_text": (
        "T-PUBTEXT",
        "Art. 50(4)",
        "Disclose AI-generated text published to inform the public (unless human editorial control)",
    ),
}
TRANSPARENCY_ROLE = {
    "T-INTERACT": "provider",
    "T-MARKING": "provider",
    "T-EMOTION": "deployer",
    "T-DEEPFAKE": "deployer",
    "T-PUBTEXT": "deployer",
}

GPAI_OBLIGATIONS = [
    ("GPAI-DOC", "Art. 53(1)(a)", "Technical documentation of the model for the AI Office"),
    ("GPAI-DOWNSTREAM", "Art. 53(1)(b)", "Information and documentation for downstream providers"),
    ("GPAI-COPYRIGHT", "Art. 53(1)(c)", "Policy to comply with EU copyright law, including opt-outs"),
    ("GPAI-SUMMARY", "Art. 53(1)(d)", "Public summary of the content used for training"),
]
GPAI_SYSTEMIC = [
    ("GPAI-EVAL", "Art. 55(1)(a)", "Model evaluation including adversarial testing"),
    ("GPAI-SYSRISK", "Art. 55(1)(b)", "Assess and mitigate systemic risks"),
    ("GPAI-INCIDENT", "Art. 55(1)(c)", "Track and report serious incidents to the AI Office"),
    ("GPAI-SECURITY", "Art. 55(1)(d)", "Adequate cybersecurity for the model and its infrastructure"),
]

# Art. 99 maximum fines (the lower of the two amounts applies to SMEs and small mid-caps).
PENALTIES = {
    "prohibited": "up to EUR 35 million or 7% of worldwide annual turnover",
    "obligations": "up to EUR 15 million or 3% of worldwide annual turnover",
    "information": "up to EUR 7.5 million or 1% of worldwide annual turnover",
}
