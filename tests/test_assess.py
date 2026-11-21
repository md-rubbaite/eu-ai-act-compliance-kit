from datetime import date
from pathlib import Path

import pytest

from aiact import assess, parse_profile
from aiact import rules as R

TODAY = date(2026, 11, 22)


def profile(tmp_path: Path | None = None, **sections):
    data = {"system": {"name": "S", "role": ["provider", "deployer"], **sections.pop("system", {})}}
    data["use"] = sections.pop("use", {})
    data["evidence"] = sections.pop("evidence", {})
    return parse_profile(data, base_dir=tmp_path or Path("."))


def ids(a):
    return {s.obligation.id for s in a.obligations}


def status(a, oid):
    return next(s for s in a.obligations if s.obligation.id == oid)


# ---------------------------------------------------------------- tiers


def test_plain_system_is_minimal_with_only_ai_literacy():
    a = assess(profile(), TODAY)
    assert a.tier == "minimal"
    assert ids(a) == {"LITERACY"}
    assert status(a, "LITERACY").applies


def test_annex_iii_employment_is_high_risk_from_december_2027():
    a = assess(profile(use={"annex_iii": ["employment"]}), TODAY)
    assert a.tier == "high-risk"
    s = status(a, "HR-RISK")
    assert s.obligation.applies_from == date(2027, 12, 2)
    assert not s.applies
    assert s.days_until == 375


def test_annex_i_product_is_high_risk_from_august_2028():
    a = assess(profile(use={"annex_i_product": True}), TODAY)
    assert status(a, "HR-TECHDOC").obligation.applies_from == date(2028, 8, 2)


def test_annex_i_and_iii_use_the_earlier_date():
    a = assess(profile(use={"annex_i_product": True, "annex_iii": ["education"]}), TODAY)
    assert status(a, "HR-QMS").obligation.applies_from == R.ANNEX_III


def test_high_risk_obligations_apply_once_the_date_passes():
    a = assess(profile(use={"annex_iii": ["credit_scoring"]}), date(2027, 12, 2))
    assert status(a, "HR-DATA").applies


@pytest.mark.parametrize("area", sorted(R.ANNEX_III_AREAS))
def test_every_annex_iii_area_is_high_risk(area):
    assert assess(profile(use={"annex_iii": [area]}), TODAY).tier == "high-risk"


# ---------------------------------------------------------------- Art. 6(3)


def test_art6_3_exemption_downgrades_and_adds_documentation_duties():
    a = assess(profile(use={"annex_iii": ["employment"], "art6_3_condition": "preparatory"}), TODAY)
    assert a.tier == "minimal"
    assert {"EX-DOC", "EX-REGISTER"} <= ids(a)
    assert "HR-RISK" not in ids(a)
    assert any("own assessment" in w for w in a.warnings)


def test_art6_3_exemption_is_ignored_when_the_system_profiles_people():
    a = assess(
        profile(use={"annex_iii": ["employment"], "art6_3_condition": "narrow_procedural", "profiling": True}), TODAY
    )
    assert a.tier == "high-risk"
    assert any("always high-risk" in w for w in a.warnings)


def test_art6_3_duties_are_for_providers_only():
    p = profile(system={"role": ["deployer"]}, use={"annex_iii": ["education"], "art6_3_condition": "improve_human"})
    assert "EX-DOC" not in ids(assess(p, TODAY))


# ---------------------------------------------------------------- roles, FRIA, workplace


def test_roles_filter_obligations():
    provider = assess(profile(system={"role": ["provider"]}, use={"annex_iii": ["employment"]}), TODAY)
    deployer = assess(profile(system={"role": ["deployer"]}, use={"annex_iii": ["employment"]}), TODAY)
    assert "HR-QMS" in ids(provider) and "DEP-USE" not in ids(provider)
    assert "DEP-USE" in ids(deployer) and "HR-QMS" not in ids(deployer)
    assert "LITERACY" in ids(provider) and "LITERACY" in ids(deployer)


@pytest.mark.parametrize(
    ("system", "areas", "expected"),
    [
        ({}, ["credit_scoring"], True),
        ({}, ["insurance_pricing"], True),
        ({}, ["employment"], False),
        ({"public_body": True}, ["education"], True),
        ({"provides_public_service": True}, ["essential_services"], True),
        ({"public_body": True}, ["critical_infrastructure"], False),
    ],
)
def test_fundamental_rights_impact_assessment(system, areas, expected):
    a = assess(profile(system=system, use={"annex_iii": areas}), TODAY)
    assert ("DEP-FRIA" in ids(a)) is expected


def test_workplace_use_requires_informing_workers():
    a = assess(profile(use={"annex_iii": ["employment"], "workplace": True}), TODAY)
    assert "DEP-WORKERS" in ids(a)


# ---------------------------------------------------------------- Article 5


def test_emotion_recognition_at_work_is_prohibited_and_in_force():
    a = assess(profile(use={"emotion_recognition": True, "workplace": True, "annex_iii": ["biometrics"]}), TODAY)
    assert a.tier == "prohibited"
    assert [p[0] for p in a.prohibited_now] == ["emotion_recognition_work_education"]


def test_emotion_recognition_for_safety_is_not_prohibited():
    a = assess(
        profile(
            use={
                "emotion_recognition": True,
                "workplace": True,
                "medical_or_safety_purpose": True,
                "annex_iii": ["biometrics"],
            }
        ),
        TODAY,
    )
    assert a.tier == "high-risk"
    assert not a.prohibited


def test_sensitive_biometric_categorisation_is_prohibited():
    a = assess(profile(use={"biometric_categorisation": True, "infers_sensitive_attributes": True}), TODAY)
    assert a.prohibited_now


def test_omnibus_prohibition_only_bites_from_december_2026():
    p = profile(use={"practices": ["intimate_imagery_csam"]})
    assert assess(p, TODAY).tier == "prohibited"
    assert not assess(p, TODAY).prohibited_now
    assert assess(p, date(2026, 12, 2)).prohibited_now


def test_biometric_use_without_annex_iii_gets_a_warning():
    a = assess(profile(use={"biometric_categorisation": True}), TODAY)
    assert any("Annex III(1)" in w for w in a.warnings)


# ---------------------------------------------------------------- Article 50


def test_chatbot_disclosure_applies_since_august_2026():
    a = assess(profile(use={"interacts_with_people": True}), TODAY)
    assert a.tier == "limited"
    s = status(a, "T-INTERACT")
    assert s.applies and s.obligation.applies_from == date(2026, 8, 2)


def test_marking_gets_the_omnibus_grace_period_for_legacy_systems():
    legacy = assess(
        profile(system={"placed_on_market": "2026-05-01"}, use={"generates_synthetic_content": True}), TODAY
    )
    new = assess(profile(system={"placed_on_market": "2026-09-01"}, use={"generates_synthetic_content": True}), TODAY)
    assert status(legacy, "T-MARKING").obligation.applies_from == date(2026, 12, 2)
    assert status(legacy, "T-MARKING").days_until == 10
    assert status(new, "T-MARKING").applies


def test_deepfake_disclosure_is_a_deployer_duty():
    a = assess(profile(system={"role": ["provider"]}, use={"deepfakes": True}), TODAY)
    assert "T-DEEPFAKE" not in ids(a)
    a = assess(profile(system={"role": ["deployer"]}, use={"deepfakes": True}), TODAY)
    assert "T-DEEPFAKE" in ids(a)


def test_public_interest_text_under_editorial_control_needs_no_disclosure():
    a = assess(profile(use={"public_interest_text": True, "human_editorial_control": True}), TODAY)
    assert "T-PUBTEXT" not in ids(a)


def test_emotion_and_biometric_flags_share_one_disclosure_obligation():
    a = assess(
        profile(use={"emotion_recognition": True, "biometric_categorisation": True, "annex_iii": ["biometrics"]}), TODAY
    )
    assert [s.obligation.id for s in a.obligations].count("T-EMOTION") == 1


# ---------------------------------------------------------------- GPAI


def test_gpai_provider_obligations_and_systemic_risk():
    a = assess(profile(system={"gpai_model": True, "gpai_systemic_risk": True}), TODAY)
    assert {"GPAI-DOC", "GPAI-COPYRIGHT", "GPAI-EVAL", "GPAI-SECURITY"} <= ids(a)
    assert status(a, "GPAI-DOC").applies


def test_gpai_models_placed_before_august_2025_have_until_2027():
    a = assess(profile(system={"gpai_model": True, "gpai_placed_on_market": "2025-03-01"}), TODAY)
    assert status(a, "GPAI-SUMMARY").obligation.applies_from == date(2027, 8, 2)
    assert "GPAI-EVAL" not in ids(a)


# ---------------------------------------------------------------- evidence and gaps


def test_evidence_present_missing_and_empty(tmp_path):
    (tmp_path / "ok.md").write_text("trained 14 people")
    (tmp_path / "blank.md").write_text("  \n")
    p = profile(tmp_path, use={"interacts_with_people": True}, evidence={"LITERACY": "ok.md", "T-INTERACT": "blank.md"})
    a = assess(p, TODAY)
    assert status(a, "LITERACY").evidence == "present"
    assert status(a, "T-INTERACT").evidence == "empty"
    assert [g.obligation.id for g in a.gaps()] == ["T-INTERACT"]


def test_evidence_outside_the_project_does_not_count(tmp_path):
    outside = tmp_path / "secret.md"
    outside.write_text("x")
    project = tmp_path / "project"
    project.mkdir()
    a = assess(profile(project, evidence={"LITERACY": "../secret.md"}), TODAY)
    assert status(a, "LITERACY").evidence == "missing"


def test_horizon_pulls_upcoming_obligations_into_scope():
    a = assess(profile(use={"annex_iii": ["employment"]}), date(2027, 10, 1))
    assert {g.obligation.id for g in a.gaps()} == {"LITERACY"}
    assert "HR-RISK" in {g.obligation.id for g in a.gaps(horizon_days=90)}


def test_obligations_are_sorted_by_date():
    a = assess(profile(use={"annex_iii": ["employment"], "interacts_with_people": True}), TODAY)
    dates = [s.obligation.applies_from for s in a.obligations]
    assert dates == sorted(dates)
