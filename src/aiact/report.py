"""Render an assessment as Markdown (for people and CI summaries) or JSON (for tools)."""

from __future__ import annotations

import json

from .assess import Assessment
from .rules import PENALTIES

DISCLAIMER = (
    "Engineering support for a compliance review, based on Regulation (EU) 2024/1689 as amended by "
    "Regulation (EU) 2026/1744. Not legal advice: confirm the classification with counsel."
)

ICON = {"present": "✅ present", "missing": "❌ missing", "empty": "⚠️ empty file"}


def _when(s) -> str:
    return "applies now" if s.applies else f"from {s.obligation.applies_from.isoformat()} ({s.days_until} days)"


def to_markdown(a: Assessment, horizon_days: int = 0) -> str:
    p = a.profile
    out = [f"# EU AI Act assessment: {p.name}", ""]
    out.append(f"- **Assessed as of:** {a.as_of.isoformat()}")
    out.append(f"- **Role(s):** {', '.join(p.roles)}")
    out.append(f"- **Risk tier:** **{a.tier}**")
    if a.prohibited:
        fine = PENALTIES["prohibited"]
        for _, article, text, start in a.prohibited:
            state = "in force" if start <= a.as_of else f"prohibited from {start.isoformat()}"
            out.append(f"- **STOP — {article}:** {text} ({state}; fines {fine})")
    out += ["", "## Why", ""]
    out += [f"- **{f.article}** — {f.text}" for f in a.reasons] or ["- No AI Act trigger declared beyond AI literacy."]
    if a.warnings:
        out += ["", "## Check", ""] + [f"- {w}" for w in a.warnings]
    out += [
        "",
        "## Obligations",
        "",
        "| Id | Article | Obligation | Who | When | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for s in a.obligations:
        o = s.obligation
        ev = ICON[s.evidence] + (f" `{s.evidence_path}`" if s.evidence_path else "")
        out.append(f"| {o.id} | {o.article} | {o.title} | {o.role} | {_when(s)} | {ev} |")
    gaps = a.gaps(horizon_days)
    out += ["", "## Gaps", ""]
    if gaps:
        scope = "now" if horizon_days == 0 else f"now or within {horizon_days} days"
        out.append(f"{len(gaps)} obligation(s) due {scope} have no evidence:")
        out += [f"- **{o.id}** ({o.article}): {o.title} — e.g. {o.evidence_hint}" for o in (g.obligation for g in gaps)]
    else:
        out.append("None in scope.")
    out += ["", f"_{DISCLAIMER}_", ""]
    return "\n".join(out)


def to_json(a: Assessment, horizon_days: int = 0) -> str:
    gaps = {g.obligation.id for g in a.gaps(horizon_days)}
    data = {
        "system": a.profile.name,
        "as_of": a.as_of.isoformat(),
        "roles": list(a.profile.roles),
        "tier": a.tier,
        "prohibited": [
            {"id": i, "article": art, "practice": t, "from": d.isoformat(), "in_force": d <= a.as_of}
            for i, art, t, d in a.prohibited
        ],
        "reasons": [{"article": f.article, "text": f.text} for f in a.reasons],
        "warnings": a.warnings,
        "obligations": [
            {
                "id": s.obligation.id,
                "article": s.obligation.article,
                "title": s.obligation.title,
                "role": s.obligation.role,
                "applies_from": s.obligation.applies_from.isoformat(),
                "applies": s.applies,
                "evidence": s.evidence,
                "evidence_path": s.evidence_path,
                "gap": s.obligation.id in gaps,
            }
            for s in a.obligations
        ],
        "disclaimer": DISCLAIMER,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
