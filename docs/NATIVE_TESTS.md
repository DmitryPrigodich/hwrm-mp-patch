# Manual native validation

[Русский](ru/NATIVE_TESTS.md)

Use an exact identified package and fresh matches for all four races. Check ordinary and Cataclysm modes, panels/languages, building, ownership changes and saves. Automatic verdicts do not replace human observations.

Priorities: [acceptance checklist](CLOSURE_CHECKLIST.md) and [known defects](KNOWN_ISSUES.md). For SU record displayed used/limit, queue state, RU spent and actual completion. Separate exact-fit,1SU insufficient/spare, two producers, cancellation, pause, producer loss and released capacity. IsBuilding alone does not prove production started.

tools/native_checks.py creates a local result record from autotests/manual-cases.ru.json without launching. This explicitly Russian operator dataset includes historical research hypotheses; use current rules for actual values, not old installation statuses. The preceding detailed guide remains [archived](archive/2026-10-30/PREVIOUS_NATIVE_TESTS.md).

Record version, all archive hashes, Game Type, map, Unit Cap, race, language, actions and reproducibility. Use not_run/blocked/partial when evidence is missing; preserve negative outcomes. Raw logs, saves and process data stay outside Git.
