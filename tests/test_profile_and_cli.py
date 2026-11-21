import json
from pathlib import Path

import pytest

from aiact import ProfileError, load_profile, parse_profile
from aiact.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({}, "missing [system]"),
        ({"system": {"role": ["provider"]}}, "system.name"),
        ({"system": {"name": "x", "role": []}}, "at least one"),
        ({"system": {"name": "x", "role": ["importer"]}}, "unknown value"),
        ({"system": {"name": "x", "role": "provider"}, "use": {"annex_iii": ["hiring"]}}, "unknown value"),
        ({"system": {"name": "x", "role": "provider"}, "use": {"profilling": True}}, "unknown key"),
        ({"system": {"name": "x", "role": "provider"}, "use": {"profiling": "yes"}}, "true or false"),
        ({"system": {"name": "x", "role": "provider", "placed_on_market": "May 2026"}}, "ISO date"),
        ({"system": {"name": "x", "role": "provider", "gpai_systemic_risk": True}}, "requires"),
        ({"system": {"name": "x", "role": "provider"}, "use": {"art6_3_condition": "preparatory"}}, "only applies"),
        (
            {"system": {"name": "x", "role": "provider"}, "use": {"annex_iii": ["education"], "art6_3_condition": "x"}},
            "not one of",
        ),
    ],
)
def test_profile_validation(data, message):
    with pytest.raises(ProfileError, match=message.replace("[", r"\[")):
        parse_profile(data)


def test_role_may_be_a_single_string_and_duplicates_collapse():
    p = parse_profile({"system": {"name": "x", "role": "deployer"}, "use": {"annex_iii": ["education", "education"]}})
    assert p.roles == ("deployer",)
    assert p.annex_iii == ("education",)


def test_invalid_toml_is_a_profile_error(tmp_path):
    bad = tmp_path / "bad.toml"
    bad.write_text("[system\nname=")
    with pytest.raises(ProfileError, match="invalid TOML"):
        load_profile(bad)


def test_examples_load():
    for path in EXAMPLES.glob("*.toml"):
        load_profile(path)


def test_cli_high_risk_example_passes_today(capsys):
    assert main(["assess", str(EXAMPLES / "cv-screening.toml"), "--as-of", "2026-11-22"]) == 0
    out = capsys.readouterr().out
    assert "**high-risk**" in out
    assert "from 2027-12-02 (375 days)" in out


def test_cli_horizon_turns_upcoming_gaps_into_a_failure(capsys):
    code = main(["assess", str(EXAMPLES / "cv-screening.toml"), "--as-of", "2027-10-01", "--horizon", "90"])
    assert code == 1
    assert "HR-TECHDOC" in capsys.readouterr().out


def test_cli_marking_gap_appears_when_the_grace_period_ends(tmp_path, capsys):
    path = tmp_path / "bot.toml"
    path.write_text(
        '[system]\nname = "bot"\nrole = "provider"\nplaced_on_market = "2026-05-15"\n'
        "[use]\ngenerates_synthetic_content = true\n"
        '[evidence]\nLITERACY = "plan.md"\n'
    )
    (tmp_path / "plan.md").write_text("training plan")
    assert main(["assess", str(path), "--as-of", "2026-12-01"]) == 0
    assert main(["assess", str(path), "--as-of", "2026-12-02"]) == 1
    assert "T-MARKING" in capsys.readouterr().out


def test_cli_complete_example_keeps_passing_after_the_grace_period():
    assert main(["assess", str(EXAMPLES / "support-chatbot.toml"), "--as-of", "2027-01-15"]) == 0


def test_cli_prohibited_practice_exits_3(capsys):
    assert main(["assess", str(EXAMPLES / "emotion-at-work.toml"), "--as-of", "2026-11-22"]) == 3
    assert "STOP — Art. 5(1)(f)" in capsys.readouterr().out


def test_cli_worst_exit_code_wins_across_profiles(capsys):
    paths = [str(EXAMPLES / n) for n in ("support-chatbot.toml", "emotion-at-work.toml")]
    assert main(["assess", *paths, "--as-of", "2026-11-22"]) == 3


def test_cli_json_output_is_machine_readable(tmp_path):
    out = tmp_path / "r.json"
    args = ["assess", str(EXAMPLES / "cv-screening.toml"), "--as-of", "2027-12-02", "--format", "json"]
    code = main([*args, "--output", str(out)])
    data = json.loads(out.read_text())
    assert code == 1
    assert data["tier"] == "high-risk"
    risk = next(o for o in data["obligations"] if o["id"] == "HR-RISK")
    techdoc = next(o for o in data["obligations"] if o["id"] == "HR-TECHDOC")
    assert risk["applies"] and not risk["gap"] and risk["evidence"] == "present"
    assert techdoc["gap"] and techdoc["applies_from"] == "2027-12-02"


def test_cli_profile_errors_exit_2(tmp_path, capsys):
    bad = tmp_path / "p.toml"
    bad.write_text('[system]\nname = "x"\nrole = ["seller"]\n')
    assert main(["assess", str(bad)]) == 2
    assert "unknown value" in capsys.readouterr().err
    assert main(["assess", str(tmp_path / "missing.toml")]) == 2


def test_cli_rejects_negative_horizon():
    assert main(["assess", str(EXAMPLES / "support-chatbot.toml"), "--horizon", "-1"]) == 2


def test_cli_catalog_lists_accepted_values(capsys):
    assert main(["catalog"]) == 0
    out = capsys.readouterr().out
    assert "credit_scoring" in out and "preparatory" in out and "social_scoring" in out
