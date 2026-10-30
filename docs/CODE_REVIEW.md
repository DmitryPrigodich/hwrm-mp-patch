# Code review — 30 October 2026

[Русский](ru/CODE_REVIEW.md)

Reviewed the integral-ceiling update and diagnostic/documentation changes against the previously published2.4.5: bugs/regressions, Lua4/API boundaries, ordinary behavior, optimization, readability, maintainability, localization, packaging and code-only publication. The owner authorized Git/Workshop updates with explicit disclosure of SU limitations.

## Findings and actions

- **Known product defect remains:** native small fractional weights do not enforce nominal SU. Human early refusal and guarded backend paid overflow are confirmed. Integral ceilings do not repair this; no exact-SU or stability claim is made. [Known issues](KNOWN_ISSUES.md).
- **Fixed stale diagnostic logs:** a repeated world/package token could accept a preceding endpoint and close an unfinished owned test. Collection now requires changed captured content and launch-time freshness before terminal closure. The digest uses the same byte snapshot, avoiding a second-read race. Offline regressions cover stale/touched content, old timestamps, missing/legacy records, fresh UTF16 and dynamic Lua errors.
- **Fixed false production evidence:** IsBuilding may indicate a waiting queue. Paid RU/completion now distinguish started production; two queue flags cannot pass cross-producer progress. An offline Lua fixture checks waiting versus paid/completed behavior.
- **Fixed budget-bound diagnostic data:** Equal fixtures derive their exact-fit baseline from the frozen source's Normal ceiling (1885/1900 or1905/1920); frozen ship prices must match, and unsupported baselines/profile selections are rejected. Historical logs are not rewritten.
- **Fixed documentation packaging:** canonical readmes and paired current EN/RU pages now render correct flat-release links. Historical investigations are archived; descriptive provenance is Markdown, functional prices/pins/receipts remain JSON. The unchanged Russian manual-case manifest is explicitly language-labeled and candidate records now support --candidate.
- **Fixed cover metadata:** preview-spec still described the old2.4cover. It now matches the unchanged owner-approved2.4.5cover and actual hashes. No image bytes changed.
- **Added configuration consistency:** integral ceiling and native_scale agreement guards reject unsupported inputs. No ship-stat/cost changes or ordinary-mode changes were introduced. Runtime performance code remains unchanged; the simple1s owned-fleet HUD was not expanded.

## Verification and scope

The entire1195-file runtime is hash-identical to the approved ceiling candidate. Relative to the earlier published runtime, only five caps, the HUD budget table and its hidden initial placeholder differ.113ship types retain ordinary fields/calls.214runtime Lua4 parses,2diagnostic template parses,360exact padding plans, effect/install fixtures and all7full archive extraction comparisons passed. 47current Markdown pages and 41release documents pass relative-link checks. Diagnostic worlds/private clones are excluded from normal runtime.

Fix `404321717a16d9af37d061be8e4f0a71c84d55e1d131c38e643c76d45aafa4ed`; local primary `857998d8b4cd5f6ce1adee9bac65a71ceedbe1de010bcac4ac617cfd33d94d7b`/81580097bytes. Archive binary identity may change while extracted payload remains identical; multiplayer peers should use matching Workshop archives.

No new native game run or local installation was performed for this ceiling/documentation revision. Earlier native evidence retains its own identities. UI overflow, simultaneous producer reservations, saves/mode switching, two-client sync and full matches remain unverified. Current publication state: [release report](WORKSHOP_RELEASE.md); earlier review chronology is [archived](archive/README.md).
