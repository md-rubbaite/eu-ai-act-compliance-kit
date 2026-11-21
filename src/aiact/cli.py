"""aiact: classify AI systems under the EU AI Act and gate releases on missing evidence.

Exit codes: 0 no gaps in scope, 1 evidence gaps, 2 usage or profile error, 3 a prohibited practice is in force.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .assess import assess
from .model import ProfileError, load_profile
from .report import to_json, to_markdown
from .rules import ANNEX_III_AREAS, ART6_3_CONDITIONS, PROHIBITED_PRACTICES


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"'{value}' is not YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aiact", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("assess", help="assess one or more system profiles")
    a.add_argument("profiles", nargs="+", type=Path)
    a.add_argument("--as-of", type=_date, default=None, help="assessment date (default: today)")
    a.add_argument(
        "--horizon", type=int, default=0, metavar="DAYS", help="also treat obligations due within DAYS as gaps"
    )
    a.add_argument("--format", choices=("markdown", "json"), default="markdown")
    a.add_argument("--output", type=Path, help="write the report to a file instead of stdout")

    sub.add_parser("catalog", help="list the values accepted in a profile")
    return p


def _catalog() -> str:
    lines = ["Annex III areas (use.annex_iii):"]
    lines += [f"  {k:24} {v}" for k, v in ANNEX_III_AREAS.items()]
    lines += ["", "Art. 6(3) conditions (use.art6_3_condition):"]
    lines += [f"  {k:24} {v}" for k, v in ART6_3_CONDITIONS.items()]
    lines += ["", "Prohibited practices (use.practices):"]
    lines += [f"  {k:36} {v[0]} {v[1]}" for k, v in PROHIBITED_PRACTICES.items()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        print(_catalog())
        return 0

    if args.horizon < 0:
        print("aiact: --horizon must be zero or positive", file=sys.stderr)
        return 2
    as_of = args.as_of or date.today()
    reports, code = [], 0
    for path in args.profiles:
        try:
            profile = load_profile(path)
        except (OSError, ProfileError) as exc:
            print(f"aiact: {exc}", file=sys.stderr)
            return 2
        result = assess(profile, as_of)
        if result.prohibited_now:
            code = 3
        elif result.gaps(args.horizon) and code == 0:
            code = 1
        render = to_json if args.format == "json" else to_markdown
        reports.append(render(result, args.horizon))

    text = ("\n" if args.format == "json" else "\n---\n\n").join(reports)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
