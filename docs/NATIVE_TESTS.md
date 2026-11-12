# Manual native validation

[Русский](ru/NATIVE_TESTS.md)

Use an exact identified 2.4.6 package and fresh ordinary matches for all four races. Check menus, panels, languages, building, research, ownership changes and saves. SU and the Cataclysm mode are excluded: the mode selector, HUD, build prices and ship descriptions must have no SU additions. Classic class limits must apply, including probes and carriers.

Priorities: [acceptance checklist](CLOSURE_CHECKLIST.md) and [known issues](KNOWN_ISSUES.md). Start with a menu-to-match smoke test in Russian and English, then check ordinary and doubled starting fleets: Hiigarans and Vaygr each start with six collectors. Verify production starts, spends RU and completes; test cancellation and two producers. IsBuilding alone does not prove production started. Exercise gravity release, transport, capture, Dock and missile interception using the detailed cases.

`tools/native_checks.py --new-run Russian --candidate` creates a local result record from `autotests/manual-cases.ru.json` without launching. This Russian operator dataset includes research hypotheses; take current values from the implemented rules. Its records start as `not_run`. The earlier SU procedure remains [archived](archive/2026-10-30/PREVIOUS_NATIVE_TESTS.md) and is not acceptance for this candidate.

Record version, all archive hashes, Game Type, map, Unit Cap, race, language, actions and reproducibility. Use not_run/blocked/partial when evidence is missing; preserve negative outcomes. Offline tests and archive comparisons do not establish native startup or multiplayer stability. Raw logs, saves and process data stay outside Git.
