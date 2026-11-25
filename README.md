# eu-ai-act-compliance-kit

[![ci](https://github.com/md-rubbaite/eu-ai-act-compliance-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/md-rubbaite/eu-ai-act-compliance-kit/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen)
![license](https://img.shields.io/badge/license-MIT-green)

**Know which EU AI Act duties apply to each AI system, from which date, and which ones you cannot evidence yet. Then let CI enforce it.**

`aiact` reads a short TOML profile of an AI system and returns its risk tier, the reasons with article
references, every obligation for your role with its application date, and the evidence you have or are
missing. It exits non-zero when a duty that already applies has no evidence, or when a prohibited
practice is declared, so it can gate a release.

The dates follow the AI Act **as amended by the Digital Omnibus on AI (Regulation (EU) 2026/1744, in force
27 July 2026)**, which moved the high-risk deadlines.

## The problem

Most teams shipping AI into the EU are unsure which parts of the AI Act reach them and when. The
deadlines moved in 2026, the obligations differ for providers and deployers, and the evidence ends up
scattered across wikis. A spreadsheet goes stale the day it is written; a check that runs in the
pipeline does not.

## What applies when

| Date | What starts to apply | Status on 22 Nov 2026 |
|---|---|---|
| 2 Feb 2025 | Prohibited practices (Art. 5); AI literacy (Art. 4, softened by the Omnibus) | in force |
| 2 Aug 2025 | General-purpose AI model obligations (Art. 53, 55); penalties | in force |
| 2 Aug 2026 | Transparency duties (Art. 50): chatbots, deep fakes, public-interest text, emotion recognition | in force |
| 2 Dec 2026 | Art. 50(2) marking for generative systems already on the market before 2 Aug 2026; new prohibition on generating non-consensual intimate imagery and CSAM | in 10 days |
| 2 Aug 2027 | GPAI models placed on the market before 2 Aug 2025 | upcoming |
| 2 Dec 2027 | High-risk systems listed in Annex III (employment, credit, education, biometrics, …) | upcoming |
| 2 Aug 2028 | High-risk AI in products covered by Annex I law (medical devices, machinery, …) | upcoming |

Details and sources: [docs/timeline.md](docs/timeline.md).

## Quick start

```bash
pip install .
aiact assess examples/cv-screening.toml          # Markdown report, exit code for CI
aiact assess examples/*.toml --format json       # one JSON document per system
aiact assess my-system.toml --horizon 180        # also fail on duties due in the next 180 days
aiact catalog                                    # accepted Annex III areas, Art. 6(3) conditions, practices
```

A profile describes the system, your role and the evidence you hold:

```toml
[system]
name = "TalentRank CV screening"
role = ["provider", "deployer"]
placed_on_market = "2026-03-01"

[use]
annex_iii = ["employment"]
profiling = true
interacts_with_people = true
workplace = true

[evidence]
LITERACY = "evidence/ai-literacy-plan.md"
T-INTERACT = "evidence/chat-disclosure.md"
HR-RISK = "evidence/risk-register.md"
```

Excerpt of the report for that profile, as of 22 Nov 2026:

```text
- Risk tier: high-risk
- Art. 6(2), Annex III — Annex III(4) Employment: recruitment, selection, promotion, …
| LITERACY   | Art. 4      | … | both     | applies now                | ✅ present |
| T-INTERACT | Art. 50(1)  | … | provider | applies now                | ✅ present |
| HR-TECHDOC | Art. 11     | … | provider | from 2027-12-02 (375 days) | ❌ missing |
| DEP-WORKERS| Art. 26(7)  | … | deployer | from 2027-12-02 (375 days) | ❌ missing |
```

## What it decides

| Question | Rule applied |
|---|---|
| Is a practice prohibited? | Declared Art. 5 practices, plus two derived checks: emotion recognition at work or in education without a medical or safety purpose (5(1)(f)); biometric categorisation inferring sensitive attributes (5(1)(g)) |
| Is it high-risk? | Annex I product → from 2 Aug 2028. Annex III area → from 2 Dec 2027, unless an Art. 6(3) condition is claimed; **a system that profiles people stays high-risk** whatever is claimed |
| Who must do what? | Provider duties (Art. 9–17, 43–49, 72–73) and deployer duties (Art. 26, 86) are filtered by the declared role |
| Is a FRIA needed? | Deployer of an Annex III system (except critical infrastructure) that is a public body or provides public services, or uses credit scoring or life/health insurance pricing (Art. 27) |
| Which transparency duties? | Art. 50(1)–(4), with the Omnibus grace period for marking by legacy generative systems; no disclosure for public-interest text under human editorial control |
| GPAI? | Art. 53 for model providers, Art. 55 if the model has systemic risk; 2 Aug 2027 for models already on the market before 2 Aug 2025 |

Evidence counts only if the file exists inside the project and is not empty, so `../` paths cannot satisfy a check.

## Use it as a release gate

| Exit code | Meaning |
|---:|---|
| 0 | No evidence gaps in scope |
| 1 | An obligation that applies (or is due within `--horizon` days) has no evidence |
| 2 | Invalid profile or usage |
| 3 | A declared practice is prohibited and the prohibition is in force |

```yaml
- run: pip install git+https://github.com/md-rubbaite/eu-ai-act-compliance-kit@v1.0.0
- run: aiact assess compliance/*.toml --horizon 90 >> "$GITHUB_STEP_SUMMARY"
```

This repository's own CI does the same with the examples. The complete chatbot profile must pass. The
CV-screening profile is reported with a 400-day horizon, which lists the high-risk work still to do.
The emotion-recognition profile must be blocked with exit code 3.

## Design

- **Rules as data.** Every article, date and obligation lives in [`rules.py`](src/aiact/rules.py), so a legal reviewer can check one file and an amendment is a data change. See [ADR 0001](docs/adr/0001-rules-as-data-with-dated-obligations.md).
- **Strict profiles.** Unknown keys, unknown areas and contradictions (for example, an Art. 6(3) claim without an Annex III area) are errors, because a silent typo would hide a duty.
- **Dates, not checklists.** Every obligation carries its application date, so the same profile gives the right answer today, on 2 Dec 2026 and on 2 Dec 2027.
- **Zero runtime dependencies.** Python 3.11+ standard library only (`tomllib`).

## Tests

66 tests cover every Annex III area, the Art. 6(3) exemption and its profiling override, role filtering,
FRIA triggers, the Art. 5 derived checks, the Omnibus dates (including the marking grace period and the
new December 2026 prohibition), GPAI legacy dates, evidence that is missing, empty or outside the project,
horizons, profile validation and every CLI exit code. CI runs them on Python 3.11, 3.12 and 3.13, then
runs the compliance gate on the examples.

## Scope and limits

This is engineering support for a compliance programme, **not legal advice**. It does not decide
borderline cases: whether something is an "AI system", whether a use really falls in an Annex III area, or
whether an Art. 6(3) claim holds. It records the answer your team and counsel reached and keeps the duties
and evidence that follow from it visible. It does not cover sector law that applies alongside the AI Act
(GDPR, product safety, financial regulation), national implementation details, or harmonised standards,
which are still being finalised.

---

Author: [Rubbaite T. Hassain](https://tanvir.info.bd) ([LinkedIn](https://www.linkedin.com/in/rubbaite)) · Software Architect, Founder of [Datazo InfoTech](https://www.datazoinfotech.com.bd) · MIT License

Architecture, requirements and review by Rubbaite T. Hassain; implementation AI-assisted.
