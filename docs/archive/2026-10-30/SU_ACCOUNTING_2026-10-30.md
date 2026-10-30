# Native SU accounting — 30 October 2026

[Русский](ru/SU_ACCOUNTING_2026-10-30.md)

**Confirmed defect: the published scale32 implementation does not enforce the nominal SU budget. Scale64 is also rejected. No production fix or Workshop update was made.** The earlier description of scaling as a usable bypass of250 was premature. The visible owned-fleet sum is separate from the native admission calculation.

Nine completed native runs supply the evidence: scale32 Measure/Equal/EqualBuild/Auto; scale64 Measure/Equal/EqualBuild; isolated QuantumLow/QuantumHigh. These are valid diagnostic runs, not nine acceptance passes. Two Lua-invalid pilots and one ambiguous many-families-per-ship calibration remain preserved and excluded. The invalid pilots exposed absent AI `format` and extra return arguments from Lua `gsub`; both diagnostic faults were corrected before the accepted runs.

## Controlled fractional values

Eleven private diagnostic types clone the same stock Hiigaran probe definition and share its stock model. Each type adds exactly one test-family cost. Native mode traces and exact owned-entry counts were checked; no physical hull count is inferred from SobGroup_Count. All runs use existing Hiigaran race definitions. No production or new gameplay race is added.

The table shows four configured single-entry probes and an initially empty test family. Additional counts0/1/2/3/8/16/32/64 were also observed. Getters are read through the actual AI context, not invented SCAR bindings.

| Passed cost per entry | Mathematical sum for4 | Native getter |
|---:|---:|---:|
| 0.015625 | 0.0625 | 0 |
| 0.25 | 1 | 0 |
| 0.46875 | 1.875 | 0 |
| 0.5 | 2 | 0 |
| 0.53125 | 2.125 | 4 |
| 0.625 | 2.5 | 4 |
| 0.75 | 3 | 4 |
| 1 | 4 | 4 |
| 1.25 | 5 | 5 |
| 1.5 | 6 | 6 |
| 2.34375 | 9.375 | 9 |

For these tested values, costs at or below0.5 contribute0; costs above0.5 and below1 contribute1 per entry; larger fractional costs can accumulate. A model using those effective costs plus an integer getter matches all252 original-type measurements under32/64 and all99 isolated quantum measurements. This is an empirical description; the exact conversion site in the engine is unknown. It is not a claim about every floating-point API or an exhaustive minimum representable increment.

## Equal nominal fleets and paid production

All seven starting compositions had1885 nominal SU including two40SU carriers. Scale32 native used values were59/61/57/91/2/57/59; scale64 values29/27/29/2/2/29/29. Original and reversed spawn order agreed. CanBuild differed between equal-budget compositions. Integer max getters returned59 and29 respectively; this alone does not locate limit conversion internally.

EqualBuild attempts two interceptor squadrons sequentially. Each request calls Build only when CanBuild returns1. Under32, Destroyers/Ions/Mixed each admitted and completed BOTH15SU squadrons:1885→1900→1915, paying900RU (100000→99100). Under64, MoreFields/Fields/Ions did the same. Other compositions stalled at1885. This confirms both premature refusal and guarded native-backend overflow. Unlike the older forced tests, a negative CanBuild was never bypassed.

The backend is CPU_DoString→CanBuild→Build, not a human UI click. UI overflow, two simultaneous producers, cancellation/pause, save/load and MP synchronization remain unverified. The ordinary UI exact-fit refusal was separately reported by the owner. No crash occurred in the completed diagnostic runs; that does not certify long matches or saves.

## Reproduction and boundaries

First prepare the regular suite with `python tools/su_boundary_tests.py prepare`. Then use `python tools/su_accounting_tests.py prepare --scale 64`, `install`, and `launch Hgn_QuantumLow` / `Hgn_QuantumHigh` / `Hgn_Measure` / `Hgn_Equal` / `Hgn_EqualBuild` / `Hgn_Auto` in separate fresh processes. Repeat selected worlds with `prepare --scale 32`. `collect --close-terminal` may close only the identified owned process after a fresh-token endpoint/error. Native installation/launch requires the owner's test request. Healthy timeouts remain open. Preparation copies the immutable regular suite, retains previous manifests and fully extracts/compares all seven BIGs; final calibration preparation parsed143 Lua4 files.

The original52-world dedicated diagnostic installation and its shortcuts were restored after all owned runs closed. Normal HWMP and its launcher slot still match the published developer package; all seven subscribed Steam archives retain their published hashes. No downstream pin/build changed. Ordinary gameplay generators, SU prices and budgets were not edited. No new Git commit/push or public upload is claimed.

Machine-readable results: [su-accounting-2026-10-30.json](evidence/su-accounting.json). Raw logs, rejected packages, source copies and process metadata stay in ignored local/su-boundary-tests. Exact nominal SU enforcement requires a different mechanism or an explicitly approved approximate balance; simply changing32 to64/50/100 is not an accepted correction.
