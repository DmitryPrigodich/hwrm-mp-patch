# Known issues and validation

[Русский](ru/KNOWN_ISSUES.md)

## Cataclysm SU enforcement: confirmed defect

Small fractional ship weights after division by32 do not match nominal SU. On controlled types, weights≤0.5 contributed0 and weights between0.5 and1 contributed1 per entry; larger fractions could accumulate. This describes tested values, not every engine numeric API. The exact conversion site is unknown. Divisor64 also failed.

At the former 1900 budget, the human UI refused a15SU order at 1885SU. In separate native32/64 tests, some1885SU compositions completed two paid squadrons:1915/1900, spending900RU. EVERY Build request required CanBuild=1. This confirms guarded AI/backend overflow; human UI overflow was not separately tested. Integral budgets are not an enforcement fix.

## Other validation boundaries

- The owner confirmed startup/readable UI on the preceding runtime; the latest ceiling change has source/Lua4 validation.
- No crash occurred in completed diagnostic runs. This is not a long-match/save guarantee; the old Access Violation cause remains unknown.
- Simultaneous queue reservations, cancel/pause, damaged-squadron replenishment, capture, saves/mode switching and two-client MP are not certified.
- Old saves with active gravity wells predating the native journal may lack original ability baselines.

Report Game Type, Unit Cap, race, matching archive hashes, displayed SU, queue state, RU spent and reproduction steps. [Acceptance](CLOSURE_CHECKLIST.md). Historical methods/results: [accounting investigation](archive/2026-10-30/SU_ACCOUNTING_2026-10-30.md).
