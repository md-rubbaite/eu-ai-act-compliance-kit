"""Classify one AI system and list the obligations that apply to it, with dates and evidence status."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import rules as R
from .model import SystemProfile

TIER_ORDER = ("minimal", "limited", "high-risk", "prohibited")


@dataclass(frozen=True)
class Finding:
    article: str
    text: str


@dataclass(frozen=True)
class ObligationStatus:
    obligation: R.Obligation
    applies: bool
    days_until: int
    evidence: str  # present | missing | empty
    evidence_path: str | None

    @property
    def gap(self) -> bool:
        return self.evidence != "present"


@dataclass
class Assessment:
    profile: SystemProfile
    as_of: date
    tier: str = "minimal"
    prohibited: list[tuple[str, str, str, date]] = field(default_factory=list)  # id, article, text, from
    reasons: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    obligations: list[ObligationStatus] = field(default_factory=list)

    @property
    def prohibited_now(self) -> list[tuple[str, str, str, date]]:
        return [p for p in self.prohibited if p[3] <= self.as_of]

    def gaps(self, horizon_days: int = 0) -> list[ObligationStatus]:
        """Obligations without evidence that apply now, or within `horizon_days`."""
        return [o for o in self.obligations if o.gap and o.days_until <= horizon_days]


def _raise_tier(a: Assessment, tier: str) -> None:
    if TIER_ORDER.index(tier) > TIER_ORDER.index(a.tier):
        a.tier = tier


def _prohibited(p: SystemProfile) -> list[str]:
    found = list(p.practices)
    if (
        p.flag("emotion_recognition")
        and (p.flag("workplace") or p.flag("education_setting"))
        and not p.flag("medical_or_safety_purpose")
    ):
        found.append("emotion_recognition_work_education")
    if p.flag("biometric_categorisation") and p.flag("infers_sensitive_attributes"):
        found.append("sensitive_biometric_categorisation")
    return list(dict.fromkeys(found))


def assess(p: SystemProfile, as_of: date) -> Assessment:
    a = Assessment(profile=p, as_of=as_of)
    obligations: list[R.Obligation] = [R.LITERACY]

    # --- Article 5
    for pid in _prohibited(p):
        article, text, start = R.PROHIBITED_PRACTICES[pid]
        a.prohibited.append((pid, article, text, start))
        a.reasons.append(Finding(article, f"Prohibited practice: {text} (from {start.isoformat()})"))
        _raise_tier(a, "prohibited")

    # --- Article 6: high-risk classification
    high_risk_start: date | None = None
    if p.flag("annex_i_product"):
        high_risk_start = R.ANNEX_I
        a.reasons.append(Finding("Art. 6(1), Annex I", "Safety component of, or itself, a product under Annex I law"))
    if p.annex_iii:
        areas = "; ".join(R.ANNEX_III_AREAS[x] for x in p.annex_iii)
        if p.art6_3_condition and not p.flag("profiling"):
            a.reasons.append(
                Finding(
                    "Art. 6(3)",
                    f"Listed in Annex III ({areas}) but claimed not high-risk: "
                    f"{R.ART6_3_CONDITIONS[p.art6_3_condition]}",
                )
            )
            if "provider" in p.roles:
                obligations += R.art6_3_obligations(R.ANNEX_III)
            a.warnings.append(
                "The Art. 6(3) exemption is the provider's own assessment; it fails if the system poses a "
                "significant risk to health, safety or fundamental rights. Keep the reasoning reviewable."
            )
        else:
            if p.art6_3_condition and p.flag("profiling"):
                a.warnings.append(
                    "Art. 6(3) exemption ignored: an Annex III system that profiles natural persons "
                    "is always high-risk."
                )
            high_risk_start = min(filter(None, [high_risk_start, R.ANNEX_III]))
            a.reasons.append(Finding("Art. 6(2), Annex III", areas))

    if high_risk_start:
        _raise_tier(a, "high-risk")
        obligations += R.high_risk_obligations(high_risk_start)
        if p.flag("workplace"):
            obligations.append(R.workplace_obligation(high_risk_start))
        fria_areas = set(p.annex_iii) - {"critical_infrastructure"}
        if fria_areas and (
            p.public_body or p.provides_public_service or {"credit_scoring", "insurance_pricing"} & fria_areas
        ):
            obligations.append(R.fria_obligation(R.ANNEX_III))

    if (p.flag("emotion_recognition") or p.flag("biometric_categorisation")) and "biometrics" not in p.annex_iii:
        a.warnings.append(
            "Emotion recognition and biometric categorisation are usually Annex III(1) high-risk uses; "
            "check whether use.annex_iii should include 'biometrics'."
        )

    # --- Article 50 transparency
    seen: set[str] = set()
    for flag, (oid, article, title) in R.TRANSPARENCY_RULES.items():
        if not p.flag(flag) or oid in seen:
            continue
        if oid == "T-PUBTEXT" and p.flag("human_editorial_control"):
            a.reasons.append(
                Finding(
                    article, "AI-generated public-interest text is under human editorial control: no disclosure duty"
                )
            )
            continue
        seen.add(oid)
        start = R.TRANSPARENCY
        if oid == "T-MARKING" and p.placed_on_market and p.placed_on_market < R.TRANSPARENCY:
            start = R.MARKING_LEGACY
        obligations.append(
            R.Obligation(oid, article, title, R.TRANSPARENCY_ROLE[oid], start, "disclosure text, marking test")
        )
        a.reasons.append(Finding(article, title))
        _raise_tier(a, "limited")

    # --- Chapter V: general-purpose AI models
    if p.gpai_model:
        start = R.GPAI_LEGACY if p.gpai_placed_on_market and p.gpai_placed_on_market < R.GPAI else R.GPAI
        rows = R.GPAI_OBLIGATIONS + (R.GPAI_SYSTEMIC if p.gpai_systemic_risk else [])
        obligations += [R.Obligation(i, art, t, "provider", start, "model documentation") for i, art, t in rows]
        a.reasons.append(
            Finding("Art. 53" + (", 55" if p.gpai_systemic_risk else ""), "Provider of a general-purpose AI model")
        )

    # --- keep only what the declared roles must do, then check evidence
    for ob in obligations:
        if ob.role != "both" and ob.role not in p.roles:
            continue
        a.obligations.append(_status(p, ob, as_of))
    a.obligations.sort(key=lambda s: (s.obligation.applies_from, s.obligation.id))
    return a


def _status(p: SystemProfile, ob: R.Obligation, as_of: date) -> ObligationStatus:
    days = (ob.applies_from - as_of).days
    rel = p.evidence.get(ob.id)
    if rel is None:
        evidence = "missing"
    else:
        path = (p.base_dir / rel).resolve()
        base = p.base_dir.resolve()
        if base not in path.parents and path != base:
            evidence = "missing"  # evidence must live inside the project, never ../../etc
        elif not path.is_file():
            evidence = "missing"
        elif not path.read_text(encoding="utf-8", errors="replace").strip():
            evidence = "empty"
        else:
            evidence = "present"
    return ObligationStatus(ob, days <= 0, max(days, 0), evidence, rel)
