# HWMP 2.4.5 Cataclysm candidate

## Accepted UCS and Vaygr terminology follow-up — 29 October 2026

The human confirmed the corrected compact-UCS Russian test: all labels readable, game closed. That confirms bb668249… rendered correctly; the subsequent requested edits below are source-checked rather than a new native visual pass. No separate intermediate installation is required.

The duplicate Экипаж row is removed from the cap popup, restored to the native file. HUD updates only the top resource-panel counter. Zero-SU probes retain native per-type supply and limits4/6/8/12/24 for Small/Normal/Large/Huge/Vast; these were already present. Their cap rows are explicitly NotEmpty at indent0, without hidden Utility/NonCombat parents. All14 zero-SU definitions (10 probes +4 starting motherships) are checked against original positive caps across all five profiles; motherships retain1. No cap numbers or SU budgets changed. This source preservation check is not a fresh boundary-queue engine test.

New approved Russian Vaygr labels: Разведчик, Ракетный корвет, Минный корвет, Абордажный фрегат, Стэлс-генератор. localization/russian_ship_names.json pins the original values and approved replacements for five build IDs plus four native selected-ship/module aliases. The shared cloak-module alias is kept consistent. Both original/native names and Cataclysm private build entries use the replacements; other languages remain unchanged. Five Russian dictionaries contain35 changed entries total:26 prior Carrier corrections +9 approved labels; every other original entry is checked unchanged. Latin SU and the upper resource panel remain as accepted.

## Separate native dictionaries; title-case popup — 29 October 2026

The owner clarified Carrier/Carriers must be corrected generally in Russian and the left caption must be exactly Экипаж (no caps); the center panel stays as-is. The first UCS repair18e75438… put low stock IDs and high private IDs in one dictionary; the human screenshot showed ALL custom IDs literally, including the former working center/role. Its native completion marker was not evidence of localization loading. That rejected candidate was NOT installed. It remains preserved in isolated UnicodeUI1 and raw evidence under local/cataclysm245/unicode-fix-20261029.

Current sourcebb668249… keeps the private dictionary compact and non-overlapping:443 matching IDs in each language, all9684400..9685208. Build name/description/timed-description fields are native UCS references; runtime counters carry ASCII numbers only. Popup UCS9684402 is Экипаж: in Russian. Center title9684401, resource.lua and icon are unchanged from the owner's accepted layout.

Carrier renaming now patches26 entries in their FIVE ORIGINAL Russian UCS dictionaries (ships/events/buildresearch/HW1ships/HW1buildresearch), preserving every other entry and the complete native files. English source wording Carrier gates all replacements and inflections; actual Transport ships/corvettes are preserved. Generated full native dictionaries are ignored in Git; generator code and checks are authoritative. Original game archives are never edited. This supersedes the previous469-entry mixed-dictionary approach. Do not claim final glyph/font success before human visual confirmation. Native/parser/hash tests and visual observations remain distinct; raw $ID traces alone never prove localization rendering.

## Russian Carrier names and UCS display repair — 29 October 2026

The owner's next Russian screenshot confirms the centered resource panel, left alignment and upright crew glyph, but exposes mojibake in the left cap-popup title and Cataclysm build names. The owner explicitly keeps the center panel and requests only the left popup label ЭКИПАЖ plus Carrier/Carriers translated as Авианосец/Авианосцы. The central ЕДИНИЦЫ ПОДДЕРЖКИ title and its resource.lua/icon bytes are unchanged.

Display repair: private native UCS entries now carry all Cataclysm build names and both normal/timed descriptions. Runtime build fields contain ASCII $ID references, not concatenated UTF8 human text. Base times still derive from the generated authoritative production table. Popup title uses native UCS9684402; its separate dynamic label receives ASCII numbers only, like the already-correct center row. This prevents the byte-string path seen in the screenshot. Six dictionaries each have469 matching IDs and no English fallback.

Russian native entries containing the transport-ship wording are renamed only when their English counterparts identify Carrier, including the appropriate inflections. Actual Transport ships/corvettes are excluded. Other-language entries retain their original translations. This affects native names/cap category and associated carrier-only labels, not ship IDs, fleets, abilities, prices or caps. Latin SU is retained. Parser/source/native startup checks do not themselves certify font rendering; fresh visual acceptance of these repaired labels is still required.

## Final resource-row corrections and localization — 29 October 2026

The owner's screenshot confirmed the first RU-adjacent row was visible, but centered independently and its three-person icon vertically inverted. The corrected row binds to a new bottom-LEFT anchor on the unchanged native RU frame and uses matching left pivot; TGA UV is vertically reversed. Full titles are uppercase and localized in115 matching native dictionary entries per language (new title9684401). English: SUPPORT UNITS: X/Y; Russian: ЕДИНИЦЫ ПОДДЕРЖКИ: X/Y. The stock Russian Resource Units is ЕДИНИЦЫ РЕСУРСОВ ($2800). The owner explicitly chose Latin SU for abbreviations, including Russian ship prices/descriptions; no Cyrillic СУ substitution.

This supersedes the temporary all-English-title choice above. Current sourcefixf2ee1e66… keeps prices/budgets/carrier count caps unchanged. Screenshot confirms the prior row's presence; final left alignment/icon orientation still need visual acceptance. The normal accepted counter/build-price behavior remains as previously confirmed. Native test and installation identities are recorded separately below/in NEXT_SESSION; no publication or consumer changes.

## Requested resource-panel layout — 29 October 2026

The owner requested moving the accepted counter under Resource Units and naming it exactly **Support Units: X/Y**, with a gold three-person crew glyph: one abstract bust in front, two behind. The generator restores the original NewTaskbar byte-for-byte and appends an SU row to the stock ResourceMenu. It follows the stock Taskbar_ResourceBottomCenter3 anchor, shares the RU font/border/spacing, and separates the static title from the gold dynamic value. The row is hidden in ordinary modes. The cap-popup counterpart is retained with the same full title.

The new glyph is original geometric source generated by tools/support_units_icon.py (standard library only) into a transparent128x12832-bit TGA, using the native RU gold/orange palette. No stock atlas is modified. Only generator code is versioned; the generated image remains excluded from Git. The requested exact English resource title is used across locale variants; ship price/tooltips remain separately translated.

Earlier human visual acceptance applies to the working counter/build prices before this placement change. The new resource-panel placement needs separate visual acceptance; native/parser checks and a glyph preview cannot prove its final alignment in the game. No price, budget, carrier cap or capacity-bonus rule changes here.

## Current UI acceptance — 29 October 2026

Sourcefix0e02b701… passed the corrected native callback fixture (50 SU, Normal), a normal startup with movies enabled, and a real Cataclysm multiplayer-map start. The owner confirmed both build prices and the total counter visible; the journal recorded64/1450 ->70/1450 on Small. Repeated HUD source loading is now guarded. This supersedes earlier UI-unconfirmed status. The old Access Violation's cause remains unknown; it did not recur in this run. No claim is made for budget enforcement, queues, fractional supply, saves or two-client sync. The counter charges nominal owned batches and excludes queues. The isolated test added print traces only; those are absent from the normal package. All raw journals stay outside Git.

[Русский](ru/CATACLYSM_2_4_5.md)

Prepared on 28 October 2026 at the owner's request. This is an experimental Game Type inside the existing HWMP package, using the four existing races and ship IDs. The first candidate was installed locally at the owner's request and entered a match, but the SU counter was missing. The latest combined UI candidate67eb6ee7… failed the human startup test and is rejected. Both local slots are restored to42b15cb8…; build prices and total HUD are unavailable in that restored version. Workshop remains2.4.1.

Select **HWMP 2.4.5 Cataclysm** in Game Type, then choose Unit Cap normally. The three ordinary HWMP Game Types remain available. Cataclysm replaces combat and economy class supplies with one weighted Support Units budget. Carrier and shipyard count caps remain, as do mothership, research-slot and zero-price probe restrictions. Layout supplies remain unchanged.

| Unit Cap | Initial SU budget |
|---|---:|
| Small (Low) | 1450 |
| Normal | 1900 |
| Large | 2600 |
| Huge | 3850 |
| Vast | 7650 |

These are provisional common budgets derived from the maximum weighted feasible old-cap fleet across the four races, rounded up to 50 SU. [Prices and calculation](SUPPORT_UNITS_TABLE_2026-10-28.md); machine-readable active inputs: `design/cataclysm.json` (113 ship types). One full native batch is charged the per-hull price multiplied by its configured batch size. Carrier: 40 SU; shipyard: 50 SU; initial mothership: 0 SU. Carriers add no capacity. Their existing race/profile count caps are preserved: Vaygr Normal is 4, Huge is 5; the previously discussed divisor 6 belonged to the abandoned capacity-bonus proposal.

The latest candidate adds **Owned fleet SU** below the objectives and in the unit-cap popup. This informational row sums current owned squadron entries at full nominal batch price. It does not count queued reservations or prove the number of surviving hulls in damaged squadrons. Native supply is responsible for queue admission and enforcement; that behavior needs an engine test.

The menu has four native white emblems in order: Hiigaran, Vaygr, Taiidan, Kushan. The Kushan badge is copied byte-for-byte from the original game and remains an ignored generated asset.

## Implementation and source checks

`tools/cataclysm.py` generates the new rules, properties, cap profiles, ship supply branches and HUD from `design/cataclysm.json` and authoritative native/donor inputs. Ship definitions read `getRulesNum(NewShipType, "hwmp_cataclysm", 0)` at configuration load. The new rules supply that property; ordinary configurations retain their original supply calls. No new race definitions or parallel ship IDs are added.

Native supply values are scaled by 32 using exact binary fractions, keeping even Vast below 250 internal units; the HUD shows full SU values. Both fractional enforcement and rule-property loading must be validated in HWRM. The scale is an implementation hypothesis, not an engine-confirmed workaround.

`tools/verify_cataclysm.py` checks all 113 configurations in both property states, unchanged ordinary fields/calls, all 20 race/profile carrier caps, HUD arithmetic with current ownership, Lua 4 syntax and the four menu emblems. The complete package also runs existing effect/localization/source regressions and full extraction/hash comparison of all seven BIGs. These checks do not certify native playability or multiplayer synchronization.

Build separately, preserving the ordinary release:

```powershell
python tools/hwmp24.py --package --candidate
```

Output: `local/HWMPPatch245-candidate` and its ZIP. The existing `local/HWMPPatch24-release` is unchanged. Preparation does not install, launch, publish or advance downstream dependency pins. The ordinary installer still targets the ordinary release; it does not implicitly install this candidate.

## Native acceptance still required

1. In a fresh process, verify menu emblems and all four Game Types. Start ordinary, Cataclysm, then ordinary again in the same process; check that static ship properties and supply do not leak across modes. This is a release blocker if the engine caches the first definition.
2. For each race, verify Normal 1900 SU, the owned-fleet row and the actual native build threshold. Test single-hull and squadron ships, several production queues, cancellation and completion at the boundary. Confirm fractional supply is not truncated.
3. Confirm an all-fighter or all-cruiser fleet reaches the shared budget without the old combat class ceilings. Verify carriers and shipyards still hit their original count limits; carriers never increase SU capacity.
4. Check Small/Large/Huge/Vast, zero-price probes and research caps, carrier docking, damaged batches, replenishment, capture, crates, death and save/load. Compare actual supply behavior with the nominal owned-group counter.
5. Use two clients with identical candidate archives, all four races and both languages of interest. Check synchronization, production admission and limit changes before any publication.

Do not infer native success from Lua mocks, parser checks or archive verification. No game or launcher was started during preparation.

## First human test and HUD correction — 28 October 2026

The original local candidate (main3cafc774…) entered a Cataclysm match. The fresh native log confirms HWMPCATACLYSM rules; the owner's screenshot shows Carriers1/3 and a working build screen, but no SU counter. This is a failed HUD acceptance, not proof of shared-budget enforcement.

The correction gives the label explicit nonzero native-scaled dimensions and a nonempty localized placeholder. It prepares text while the popup is closed and assigns text before making the row visible. Unknown profile values show `?` instead of silently suppressing the row; HUD initialization now writes the selected profile to the log. The initial empty/unsized row is a suspected cause, not a proven sole native cause.

All113 ship configurations, cap values and prices are unchanged from the first candidate. Expanded mocks cover closed-popup updates, all five profiles, unknown profiles and nonzero UI dimensions; all198 Lua4 parses and full seven-archive extraction/hash comparisons passed. The corrected display still requires a human retest. Game entry alone does not certify fractional supply, queue enforcement, damaged groups or multiplayer.

## Ship prices and second HUD correction — 28 October 2026

The owner retested main6fe3938b… and again reported no SU row. The Vaygr screenshot shows Carrier1/4, the Scout3/3 card and the build list; it is not a positive counter test. Evidence is retained locally under local/cataclysm245/ship-descriptions.

Cataclysm now shows a short price directly in build-list names, for example Survey Scout [SU:6], and a full tooltip suffix: SU:6 per squadron (3 x 2). Single-hull ships show their per-ship price. All113 selected-ship descriptions receive a short leading price through113 private native dictionary IDs, followed by the original translated role description. The selected ship's name and combat/economy parameters do not change. Prices and caps are unchanged. All six languages are generated separately; an explicit fallback report is saved locally.

The native dictionary registry preserves every stock entry and adds hwmp24_cataclysm.dat. Its localedat.lua is explicitly packaged as a data resource; the six UTF16/BOM/CRLF dictionaries stay in their native locale archives. Native data/locale aliases remain unchanged. Build labels use the rules property in the UI context and work with either production-time tooltip setting; ordinary build tables are checked unchanged.

HUD initialization is now attached to the final shared native OnInit/OnStartOrLoad callbacks, gated by Rules_GetNumber("hwmp_cataclysm",0), instead of storing callback aliases in the alternate entry point. A load-order mock checks that reloading the native base cannot erase the HUD hook and that ordinary modes do not start it. This addresses a possible initialization cause; native success remains unconfirmed. Do not describe the twice-failed counter as working before the next human test.

## Confirmed native crash and containment — 28 October 2026

The owner's launch of main0c50c185… failed. The native2.303/build3409635 log explicitly reports `attempt to call global Rules_GetNumber (a nil value)` in OnStartOrLoad26 and OnInit69, followed by a fatal SCAR exit. The function being present in the executable or older reference dumps did not prove that it existed in this SCAR context. Our mock supplied it and missed the failure.

Both local locations were first restored to the preserved6fe3938b… revision that the owner had entered successfully; that revision still lacked the SU counter. The failed package, full native log and source are retained outside the game under local/cataclysm245/crash-20261028.

The corrected candidate preserves the native deathmatch callbacks byte-for-byte and disables HUD initialization entirely. The native unit-cap popup is restored unchanged. Ship prices in the build list/tooltips and selected-unit descriptions remain; SU prices, budgets, carriers and ordinary gameplay data do not change. Tests now leave Rules_GetNumber absent and verify that both original callbacks still execute without starting the HUD. The total counter is unavailable until a supported integration is tested; do not advertise it as working. The corrected package still needs native confirmation, which is distinct from its source/archive checks.

## Native context diagnosis and UI retest — 29 October 2026

The owner confirmed SU prices in selected-ship descriptions on main42b15cb8…, but no build prices or total counter. That revision deliberately disabled the counter after the earlier crash.

An explicitly authorized isolated native diagnostic on HWRM2.303/build3409635 confirmed that the build-data context has no UI_RulesGetNumber, GetGameSettingAsString, GameRulesName or Rules_GetNumber. The old guarded build helper therefore did nothing. The SCAR context does expose GameRulesName, the owned-squadron query, Rule_AddInterval and UI_SetTextLabelText; Rules_GetNumber remains absent. Full raw evidence stays outside Git under local/cataclysm245/context-probe.

The current generator selects a thin build-table wrapper through each existing race's Cataclysm path_build property. It loads the original build table, then appends translated SU names/tooltips without querying unavailable mode APIs. Ordinary modes continue to load their original table. The HUD now uses a plain GameRulesName comparison in the final native callbacks and a one-second timer; it writes a dedicated NewTaskbar label and the open unit-cap popup. The previously failing Rules_GetNumber call is absent.

Source checks pass for113 ship definitions in both modes,24 race/language build tables with both time-tooltip settings, missing-API callback fixtures and210 native Lua4 parses. These checks do not prove the engine selects the new path or renders the counter. The attempted isolated auto-start UI world never produced a Starting Level/result marker and is not a native pass. No claim is made for shared-budget enforcement, queues or multiplayer.

Retest a fresh skirmish with Game Type **HWMP2.4.5 Cataclysm**. Look for a price such as Survey Scout [SU:6] in construction, the full squadron price in its tooltip, and the owned-SU counter below objectives/in the fleet-cap popup. Build or lose a ship and check that the owned value changes after about one second. Normal should display a1900 SU budget. The counter excludes queues and charges damaged squadron entries their nominal full price. Use a fresh match rather than an old save for this UI check.

## Latest status — 29 October 2026

Human retest of main67eb6ee7… failed during level startup. Root cause is unknown; the last log contains no explicit Lua exception. Both local slots are restored to42b15cb8… with selected-ship prices and HUD disabled. The source above retains the failed experiment for isolation and must not be installed again as a verified fix.

### Human clarification and crash files — 29 October 2026

The human clarifies Access Violation occurs during the Gearbox startup movie, before the menu. The available HwRM.log reaches level startup and may belong to another attempt; do not infer the reported failure stage from it. Preserved29October11:21 error log/minidumps: read0x20, executable offset/address0x00548f3c, without an explicit Lua exception. Export-derived nearest stack labels are not reliable function-level symbols and do not establish a network or movie root cause. Also preserved28October21:58 ucrtbase/strnlen crash from the failed auto-start fixture; that fixture failed natively and must never be counted as a pass. Root cause remains unknown. Both normal slots now match restored42b15cb8…. Further diagnostics must be isolated from them.

The subsequent isolated component tests reached real native completion markers; Combined counted50 SU. No visual or normal-startup success is inferred. Both callback harness attempts were invalid (rejected redefinition / missing OnInit); the latter produced the diagnostic general-failure dialog. No game/launcher remains running. Details and raw evidence stay under local/cataclysm245/native-ui-isolation.
