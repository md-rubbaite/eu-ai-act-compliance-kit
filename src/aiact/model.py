"""System profile: what a team declares about one AI system, read from TOML and validated strictly."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .rules import ANNEX_III_AREAS, ART6_3_CONDITIONS, PROHIBITED_PRACTICES, ROLES


class ProfileError(ValueError):
    """The profile is incomplete or contradicts itself."""


USE_FLAGS = (
    "annex_i_product",
    "profiling",
    "interacts_with_people",
    "generates_synthetic_content",
    "emotion_recognition",
    "biometric_categorisation",
    "infers_sensitive_attributes",
    "deepfakes",
    "public_interest_text",
    "workplace",
    "education_setting",
    "medical_or_safety_purpose",
    "human_editorial_control",
)


@dataclass
class SystemProfile:
    name: str
    roles: tuple[str, ...]
    placed_on_market: date | None = None
    public_body: bool = False
    provides_public_service: bool = False
    gpai_model: bool = False
    gpai_systemic_risk: bool = False
    gpai_placed_on_market: date | None = None
    annex_iii: tuple[str, ...] = ()
    art6_3_condition: str | None = None
    practices: tuple[str, ...] = ()
    flags: dict[str, bool] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    base_dir: Path = Path(".")

    def flag(self, name: str) -> bool:
        return self.flags.get(name, False)


def _date(value: object, key: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ProfileError(f"{key}: '{value}' is not an ISO date (YYYY-MM-DD)") from exc
    raise ProfileError(f"{key}: expected a date")


def _bool(table: dict, key: str, where: str) -> bool:
    value = table.get(key, False)
    if not isinstance(value, bool):
        raise ProfileError(f"{where}.{key}: expected true or false")
    return value


def _str_list(table: dict, key: str, where: str, allowed: dict | tuple) -> tuple[str, ...]:
    value = table.get(key, [])
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ProfileError(f"{where}.{key}: expected a list of strings")
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ProfileError(f"{where}.{key}: unknown value(s) {unknown}; allowed: {sorted(allowed)}")
    return tuple(dict.fromkeys(value))


def parse_profile(data: dict, base_dir: Path = Path(".")) -> SystemProfile:
    system = data.get("system")
    if not isinstance(system, dict):
        raise ProfileError("missing [system] table")
    name = system.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ProfileError("system.name is required")
    roles = _str_list(system, "role", "system", ROLES)
    if not roles:
        raise ProfileError("system.role must name at least one of: provider, deployer")

    use = data.get("use", {})
    if not isinstance(use, dict):
        raise ProfileError("[use] must be a table")
    unknown_flags = sorted(
        k for k in use if k not in USE_FLAGS and k not in ("annex_iii", "art6_3_condition", "practices")
    )
    if unknown_flags:
        raise ProfileError(f"use: unknown key(s) {unknown_flags}")
    flags = {k: _bool(use, k, "use") for k in USE_FLAGS}

    condition = use.get("art6_3_condition") or None
    if condition is not None and condition not in ART6_3_CONDITIONS:
        raise ProfileError(f"use.art6_3_condition: '{condition}' is not one of {sorted(ART6_3_CONDITIONS)}")

    evidence = data.get("evidence", {})
    if not isinstance(evidence, dict) or not all(isinstance(v, str) for v in evidence.values()):
        raise ProfileError("[evidence] must map obligation ids to file paths")

    profile = SystemProfile(
        name=name.strip(),
        roles=roles,
        placed_on_market=_date(system.get("placed_on_market"), "system.placed_on_market"),
        public_body=_bool(system, "public_body", "system"),
        provides_public_service=_bool(system, "provides_public_service", "system"),
        gpai_model=_bool(system, "gpai_model", "system"),
        gpai_systemic_risk=_bool(system, "gpai_systemic_risk", "system"),
        gpai_placed_on_market=_date(system.get("gpai_placed_on_market"), "system.gpai_placed_on_market"),
        annex_iii=_str_list(use, "annex_iii", "use", ANNEX_III_AREAS),
        art6_3_condition=condition,
        practices=_str_list(use, "practices", "use", PROHIBITED_PRACTICES),
        flags=flags,
        evidence=dict(evidence),
        base_dir=base_dir,
    )
    if profile.gpai_systemic_risk and not profile.gpai_model:
        raise ProfileError("system.gpai_systemic_risk requires system.gpai_model = true")
    if condition and not profile.annex_iii:
        raise ProfileError("use.art6_3_condition only applies to systems listed in use.annex_iii")
    return profile


def load_profile(path: str | Path) -> SystemProfile:
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ProfileError(f"{path}: invalid TOML: {exc}") from exc
    return parse_profile(data, base_dir=path.parent)
