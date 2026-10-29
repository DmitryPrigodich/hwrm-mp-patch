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

## Final native callback repair — supersedes the pre-test identity

The first exact-package startup reached a real Cataclysm match, and the owner confirmed readable menu/match, SU counter and prices, then closed the game. Its log exposed an inherited Kushan callback load-order defect: Kus_CloakedFighter accessed MemGroup before the shared utility scan. Publication was held. Both Kushan users (cloaked fighter/drone frigate) now explicitly load their missing dependency; memgroup.lua preserves an existing registry on repeated scans. Cloaked-fighter regeneration now uses its actual self_group and compares the native numeric dock flag with zero. The original 20-tick damage window, 0.016 healing increment and cadence are unchanged. This repairs the documented stationary/out-of-combat gate; it is not a new healing coefficient.

Cold-order/reload fixtures cover both callback orders, registry preservation, valid group arguments, dock/space/speed gates, the damage window, full health and destruction. Source regressions and **214 Lua 4 parses** pass; seven BIGs again pass full extraction/hash comparison. A separate native Kushan scene loaded both callbacks (actual update markers), damaged the fighter to 0.5, observed health0.7399995923 and67SU, and reached its completion marker without traceback/callback-load errors. It changes scenario/test metadata and adds trace prints only; it is not a full multiplayer match. Its own completed process was closed after PID/diagnostic-command identity checks; no user game was stopped.

Final fix `c3b5f248f1f18a6f699a0bf6a723910532266ac164d0b5d9ffbc20ea54e7641a`; developer primary `22dfd3a7cc59054edf8b137e755fc88c7007789af61725c0e82b3f2e7dbe29d6`, 81580122 bytes. Runtime remains1195files, now237overrides. The earlier reviewed identity remains a recorded checkpoint, not the final publication identity. A final ordinary startup of this exact artifact follows before Steam upload. Expanded MP/queue/cap/save tests remain open.
