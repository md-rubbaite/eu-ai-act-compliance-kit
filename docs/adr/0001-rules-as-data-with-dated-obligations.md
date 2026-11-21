# ADR 0001: Rules as data, with an application date on every obligation

- Status: accepted
- Date: 2026-11-22

## Context

The AI Act's obligations depend on three things: what the system does, the organisation's role (provider
or deployer), and the date. The dates already changed once. The Digital Omnibus on AI (Regulation (EU)
2026/1744) moved the Annex III high-risk deadline from 2 August 2026 to 2 December 2027 and the Annex I
deadline to 2 August 2028. It also added a grace period for content marking and a new prohibition. More
guidance and standards are expected.

The tool's users are engineers and compliance leads, who need an answer they can act on in a pipeline,
and lawyers, who need to check how that answer was reached.

## Decision

1. **All legal content lives in one data module** (`rules.py`): dates, Article 5 practices, Annex III
   areas, Art. 6(3) conditions and every obligation, each with its article reference. The classification
   logic in `assess.py` contains no article text or dates.
2. **Every obligation carries its own application date.** The assessment is a function of
   `(profile, as_of)`, so the same profile can be checked for today, for a release date, or with a
   look-ahead horizon.
3. **The profile records decisions; it does not make them.** Questions that need legal judgement are
   explicit fields that the team fills in, such as `annex_iii` and `art6_3_condition`. The tool applies
   the mechanical consequences, including those that override a claim: profiling keeps an Annex III
   system high-risk.
4. **Evidence is a file path per obligation.** A file counts only if it exists inside the project and is
   not empty. Documents stay in the repository next to the system they describe and are reviewed in
   pull requests.
5. **Exit codes are part of the interface:** 0 no gaps, 1 gaps, 2 bad input, 3 prohibited practice in force.

## Consequences

- An amendment is usually a change to constants and obligation rows, reviewed in one diff, with tests
  that pin each date.
- The tool cannot tell whether a declared Annex III area is correct. Strict validation (unknown keys and
  values are errors) prevents typos but not wrong answers, so the README states that classification needs
  counsel.
- Checking that evidence exists says nothing about its quality. The gate stops *missing* work, while
  review of the documents remains a human task.
- Alternative considered: a questionnaire engine with free-text answers and scoring. Rejected because
  scores hide the legal reason; this tool always prints the article that triggered each duty.
