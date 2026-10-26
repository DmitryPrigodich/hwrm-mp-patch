# Frozen native test examples

[Русский](README.ru.md)

Text-only preservation of the HWMP diagnostic worlds, Lua4 runtime, builders, collectors and relevant effect helpers. **This directory is never read by the normal mod builder or imported by gameplay.** snapshot.json records every source path/hash; `python tools/freeze_test_examples.py` verifies it. Do not silently regenerate this reviewed snapshot.

## Where to start

| Need | Example |
|---|---|
| Autonomous case, logs and result boundaries | source/autotests/runtime.lua; source/tools/run_auto_tests.py |
| Real checkpoint staging and a cold process | SaveLoadAuto/Cold/Empty/Coop branches; run_auto_queue.py |
| Many sources, mixed baselines and pressure | journal_pressure.lua; run_auto_pressure.py |
| Dead anchors and later new fields | journal_recycle.lua |
| Paid science/production and native controls | hw1_damage.lua; research_effects.lua; production.lua |
| Capture/Dock/off-map cargo interruptions | salvage.lua; dock.lua; transport.lua |
| Missile identity and geometry fixtures | defense.lua; auto_combat_geometry.py |
| Human Extra Missions and native UCS registration | source/testgrounds; testgrounds.py; verify_testgrounds.py |
| Load-safe effect library | source/tools/templates and source/hwmp-patch-2.4/overrides/scripts/hwmp24 |

## Reuse

Read AUTO_TESTS.md, UPDATE_WORKFLOW.md and the change-specific report first. Copy the relevant source into a separate working checkout/mod and adapt its namespace, unit types, world positions and own package markers. Builders expect this repository's helpers, pinned data and a local game/Toolkit cache; this snapshot is source reference, not an asset-complete standalone game package. For exact historic reproduction use the snapshot's files together with the corresponding repository data, then revalidate inputs.

Keep private diagnostic types distinct from normal units. Use native Lua4 syntax, explicit numbered fields where record/list mixing would fail, UTF16/BOM/CRLF for new UCS, native data/locale aliases and declared diagnostic overrides. Check physical motion/orders, not a flag alone. SobGroup_Count is a squadron-entry count, not a physical hull count.

Collect fresh run/mode/hash evidence and an actual load marker; preserve failed/invalid controls. Never infer native passes from mocks or copy one world's verdict into another. Start game tests only with the owner's request, never stop unrelated games and never publish raw saves/process/profile metadata.

No binaries, models, pictures, audio, logs, saves, passwords or personal settings are included. Original Players Patch/Test21 credits remain applicable to inherited code. This archive supplies examples and limitations, not a new license for upstream assets.
