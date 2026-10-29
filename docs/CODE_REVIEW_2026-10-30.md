# Code review — HWMP 2.4.5, 30 October 2026

[Русский](ru/CODE_REVIEW_2026-10-30.md)

Reviewed against e7faaa0 (published 2.4.1): defects/regressions, Lua 4/native API boundaries, ordinary-mode behavior, localization, optimization, readability, maintainability, packaging and code-only publication. The owner authorized a code commit/push, startup recheck and conditional update of Workshop item 3827773780 with the already approved description/cover. No downstream dependency advancement is included.

## Findings resolved

- Removed three unreferenced legacy locale tables (BuildText, BuildSuffix, BuildBadge): **375,902 source bytes** across six runtime files. Executing the old/new locale Lua and comparing every remaining HWMP global proves identical active values; all other 1189 source files are hash-identical. No gameplay/cost/budget/cap values changed in this review.
- Added explicit overlap, compact-range and native-collision guards for every private UCS ID block before writing dictionaries. This prevents future roster growth from silently replacing another description block.
- Replaced the dynamic module import in Workshop staging with its explicit module reference. Candidate selection remains visible and preserves the ordinary release.
- Checked Black formatting with unchanged ASTs. Updated short EN/RU guides and readmes; preserved the complete older development chronology in docs/archive/2026-10-29 instead of leaving rollback text in the current instructions.

## Validation

113 ship configurations retain ordinary fields/calls; all Cataclysm supplies match the active design. Source checks cover 24 race/language build tables, both tooltip settings, all five profiles, retained carrier caps, 70 zero-SU ship/profile cases and 443 matching dictionary IDs in each of six languages. All **211 native Lua 4** parses pass. Existing effect-journal and installation/rollback fixtures pass. Every one of the seven rebuilt BIGs was fully extracted and hash-compared with the intended source; native data/locale aliases are checked. Runtime composition is 1195 files / 234 overrides.

Fix: `705f9fadadc76980c33164e797226bf3240115f82ace4fe8d9e74f836c6b762f`. Developer primary: `6e1f2829c1141069b3ce9b3644a5df797c661630212c8f759590beeb0ffec37a`, 81579947 bytes. Previous accepted source f6bbba2b… and main75591f28… remain backed up outside the game. The ordinary 2.4.1 release is preserved.

Approved Workshop text and preview remain byte-identical to the owner's reviewed draft. Its inherited English maintenance line has one trailing space; this formatting is deliberately preserved rather than silently changing the approved description. No asset/media/BIG/cache/raw log/save/process/profile material is included in the code commit. Generated full stock dictionaries remain ignored; only the private compact UCS dictionaries and their generators are versioned.

## Acceptance scope

Prior owner evidence confirms normal startup, changing owned SU, build prices, the RU-adjacent layout and readable Russian. A new startup check of this exact post-review package is **pending** at this code checkpoint; publication has not been submitted. Startup is distinct from weighted admission/queues, damaged batches, capture, saves, same-process mode switching, two-client sync and full-match balance. Those remain public field tests; no complete native certification is claimed. The old Access Violation root cause remains unknown.

Recommended effort: High for native compatibility/cap diagnosis; Medium for routine packaging/publication. App settings are not changed by this recommendation.
