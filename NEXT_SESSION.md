# Current handoff — 12 November 2026

## Ready candidate

On 12 November the owner explicitly confirmed removing SU while retaining code and documentation improvements. The fresh candidate was rebuilt and checked; the EN/RU native test guide now describes the ordinary modes only. Completed **HWMP 2.4.6 without SU**, preserving shared fixes/localization/ordinary balance. Source decisions: [EN](docs/REVIEW_2_4_6.md) / [RU](docs/ru/REVIEW_2_4_6.md). Current README and docs indexes lead with this result; earlier SU material is reference only.

Package: `local/HWMPPatch246-candidate` and `local/HWMPPatch246-candidate.zip`. Main SHA256 `2c28e330b30ecd834a6fcf415e1570bc86954721c7543397c7d94aeb03c17409`; ZIP `8dcb65f309138adab4e73ae3cec49b36e071a4d4a95d2802300d6954ee8d324e`. Fix `f6941b453b836532f7ec7ba15a444199c1722a9e2203c72342d6e3de092c0ef4`; content `aca324e8af1bf2e33c1e857ec4e72a84bea0c94f6efa3927d5c0f71c70f46bdb`. Fresh rebuild receipt: `local/review246/2026-11-12-rebuild.json`. The 2 November review receipts remain historical.

No Cataclysm entry, SU counter/prices, fractional supply or script gate is shipped. All 113 original ship definitions and 62 classic cap files match ordinary native behavior; other accepted improvements remain. The old 2.4.6 Test1 and design proposals are preserved separately under `local/cataclysm246`, design/ and their labeled reference docs. They are not release inputs.

## Engineering and checks

Every active Python tool rejects optimized execution. Critical source pin/path guards use explicit exceptions. Explicit build contexts isolate source/work/generated files per release variant. Portable receipts live inside packages. Fresh staging preserves prior owned packages, excludes stale files and rolls back failed promotion. Installer paths are explicit; obsolete owned documents migrate only with previous hashes and backup. Unknown/modified files remain protected. Archive ROOT is restored on exceptions.

Only two manual helpers remain under overrides, listed in manual-files.json. 223 stale generated snapshots were backed up locally and removed from tracked working files; history and all 73 frozen example files remain unchanged. Canonical effects.lua consolidates the old generated effect/journal bytes exactly; no performance change is claimed.

Passed: 13 asset-free unittest cases, Black, Pyflakes, source/mechanic/localization checks, 170 Lua 4 files, full seven-BIG extraction/hash comparison, final ZIP CRC/payload hashes and actual installed-folder read-only plan. CI workflow is prepared for push/PR with asset-free tests; no GitHub run occurred. Updated docs EN/RU and prepared Workshop descriptions explain SU removal. The candidate was subsequently installed and launched at the owner's explicit request on 12 November; live Workshop remains unchanged.

## Publication / native boundary

Live Workshop is still 2.4.5, item 3827773780, manifest 4437220967220031387 with known SU defect. On 12 November the owner explicitly requested installation and launch, then confirmed the launcher was closed. Installed the exact candidate through the owned installer; backup: local/installed-backups/20261112T002516561091Z/HWMPPatch24. Other mods and protected packages were verified unchanged. Launched Russian/windowed 1600x900 with Lua tracing (PID 8800). Fresh log confirms HWMPPatch24.big and Russian.big loaded, GameSetup callbacks and no detected fatal errors; process responds. Window capture failed twice, so visual menu/match acceptance is unconfirmed. The game was left running; never stop it yourself. Evidence and new test record: local/native-tests/20261112T002506167929Z/. Detailed cases remain not_run; no full-match or two-client acceptance. No Git commit/push, upload or downstream pin/build was performed. No crash-free guarantee is made.

Recommend Medium for routine installation/field follow-up; High if native/accounting diagnosis is reopened. App setting unchanged. Pre-change code/docs and cleanup receipt are under the campaign workspace's local/review246/before and cleanup.json; published 2.4.5 source/receipts and earlier releases remain preserved.
