# Stock model reuse in 2.4.1

[Русский](ru/ASSET_DEDUPLICATION_2_4_1.md) · [Provenance](ASSET_PROVENANCE.md)

The prepared local primary BIG is **81,519,866 bytes**, down from **109,331,829**: **27,811,963 bytes** saved (25.4%). The published 2.4 baseline remains separately preserved. This is an asset/loading maintenance change; no combat coefficients, research, starts or map previews change. Technical directories, BIG filenames and Workshop ID3827773780 stay stable. Public menu/title/rules labels advance to2.4.1 through tools/project_version.py.

## Decisions

| Resource | Decision | Evidence |
|---|---|---|
| ship/hgn_mothership/hgn_mothership.hod | Omit mod copy; use stock at the same path | Exact SHA256 equality with current HW2Ships.big. No .ship change. |
| missile/vgr_mediummissile/vgr_mediummissile.hod | Omit copy; LoadSharedModel(NewShipType,"vgr_heavymissile") | HOD bytes identical; original and stock event text identical after CRLF normalization. Only the loading call changes in .miss. |
| vgr_corvetteantifightermissile.hod and vgr_corvettesmallmissile.hod | Keep both copies | HOD bytes match stock small missiles, but their event tables use WEAPON/CORVETTE/IMPACT/WEAPON_MVETTE_MISSILE_HIT instead of the stock frigate impact sound. LoadSharedModel also selects the shared model's .events. |

The corvette copies total654,804 uncompressed bytes. Overriding the stock small missile's event table globally would affect other missile types; it is not an acceptable size-only change. HOD byte equality alone is insufficient grounds for resource-path aliasing. A [pinned Cataclysm Remastered source example](https://github.com/btraas/CataclysmRemasteredMod/blob/72c2af0dc73ff76460a6900a0c261dacee80ae92/missile/vgr_hw1heavymissile/vgr_hw1heavymissile.miss) establishes actual .miss usage of LoadSharedModel; our engine traces establish its event-file behavior here.

## Reproduction and safeguards

baseline/stock-asset-fallbacks.json pins native archive hashes, omitted and target HOD hashes, and canonical Medium event text hash. tools/stock_assets.py validates those inputs before composition. Changed assets/archives or distinct event text stop preparation. Original donor/cache/native assets remain untouched. The composed source omits exactly two HODs and changes exactly seven resources: one .miss model call plus six2.4.1 menu/rules/credits labels. All other1136-baseline resources retain their hashes. Six language dictionaries remain unchanged.

`content_revision` hashes the complete source inventory, including omissions; `fix_revision` retains its existing override-hash meaning. Workshop staging uses content_revision for its directory so a packaging-only change cannot collide with an earlier draft. Consumer submodule pins/builds are not advanced.

Run `python tools/hwmp24.py --package` for source/effect/localization checks and complete extraction comparison of all seven BIGs. The isolated `SharedModels` mode in tools/auto_testgrounds.py tests stock mothership creation and launch/impact of each missile type. It uses private single-weapon corvettes, a medium-armor frigate probe, and a strikecraft-family light-armor probe for anti-strike missiles. Test-only .events append execution traces without changing event tables; these traces and test missions never enter the normal mod.

After authorized diagnostic build/install, run `python tools/run_auto_queue.py SharedModels --wall-timeout 180`. Require four passes, zero fatal/script/weapon errors, own corvette event-file traces and shared heavy-missile event traces. The shared small-missile event trace must be absent. Keep the complete native journal locally; publish only its hash and summarized results. Lua4 parsing and installation/rollback fixtures are additional checks, not native visual/audio acceptance.

## Rejected pilots

- e08c7917…: three passes, anti-strike failed because the test incorrectly presented a frigate-family target to a strikecraft-only launcher. This was a fixture error; its failed result remains preserved.
- 52954056…: four launch/impact passes after correcting the target. Event execution traces loaded stock vgr_smallmissile.events and omitted both corvette-specific event files. The all-three-missile alias experiment was therefore rejected despite correct damage. Its journal SHA256 is2b0e72ef8a065b61a94ce19e909037279a6d698ccf64c04d780bc2ec0dc65165.

Final native acceptance and publication are recorded below after the corrected two-omission candidate runs. A laboratory pass does not certify visual rendering, audible sound quality, network sync, old saves or full matches; existing field acceptance remains applicable.

Prepared fix: `918818ee91a81a3c46bfa61b8a301649716ec16868f0a9b4da7ac2e8bb5970b7`. Content: `9fe4ce118585d5ab96154d6995d3405650187a6f132765ed0f23c14d5214638f`. Main SHA256: `722521185ac8125dedbbd5efded4981bb6ff7ed04ee1660af80cb7326e2c5d9b`. Source1134files,57overrides.

## Accepted native smoke

Final diagnostic `d3f26c9ca29c9ba45ca006fae1a19d9ee4c42cdd792423fb3c244ab5e7a21c82`: **4/4 passed**, zero fatal/script/weapon errors. Mothership exists; small/anti-strike/Medium missiles each reached peak2 and dealt75.59375/90/3240 damage in their own fixture. These are observed hit totals, not balance measurements. Own corvette event files executed; shared vgr_heavymissile.events executed; shared vgr_smallmissile.events did not. Diagnostic base inventory matches the final1134-file normal source exactly; trace-only event/UI differences are declared in its local manifest. Journal SHA256: `fda021ebbbaa00e9b6691eb2ed987651a3e909731d1ec8db7c1b8b3d4b9b94f8`. The runner closed only its completed owned process.

All52override Lua-compatible definitions parsed with the pinned Lua4compiler. Source/effect/localization regressions and installation/rollback fixtures passed; every normal BIG passed full extraction/hash comparison. Source-level guards now reject shared models whose event text differs. Public evidence is in baseline/asset-deduplication.json; raw journals/saves/process data stay local.

## Published2.4.1

Updated the same public [Workshop item3827773780](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) at2026-10-26T21:16:37+00:00; manifest2695969873528017586. Steam confirmed upload OK; the anonymous API confirms the title and visibility0. All seven archives from the actual Steam subscription download passed CRC and complete extraction/hash comparison against1134source files. The approved cover hash is unchanged. Toolkit primary: **81,973,633 bytes**, SHA256`b3b591c18d84ca2077e22b4a4fca3de0b387bb65b7d0d3203a84a7dae1fa6b6f`; total downloaded package **82,202,657 bytes**. The earlier2.4receipt is retained in workshop/releases/2.4.json; current public hashes are in workshop/published-release.json.

Local normal installation and selected launcher slot use the verified72252118… development archive; previous HWMP and the current VR slot are backed up outside the game. Original BananaDLC/other mods preserved. No ordinary game/launcher was started for this installation and no consumer source/pin/build was advanced. Network peers must use the same Workshop release; Toolkit and local BIG binary hashes differ.
