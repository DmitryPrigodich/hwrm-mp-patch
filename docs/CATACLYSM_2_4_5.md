# HWMP 2.4.5 Cataclysm

[Русский](ru/CATACLYSM_2_4_5.md)

Cataclysm is an optional Game Type inside the existing HWMP package, using the original Hiigaran, Vaygr, Kushan and Taiidan races and 113 ship types. Select **HWMP 2.4.5 Cataclysm** in skirmish/multiplayer setup. The three ordinary HWMP Game Types remain available.

## Fleet rules

Combat and economy ships consume one weighted Support Units pool instead of their old class supplies. Carrier and shipyard count caps, research slots, starting mothership limits and zero-SU probe limits remain. Carriers add no capacity; carrier cost is 40 SU, shipyard 50, starting mothership 0. Layout supplies are unchanged.

| Unit Cap | SU budget | Classic probe cap per family |
|---|---:|---:|
| Small (Low) | 1450 | 4 |
| Normal | 1900 | 6 |
| Large | 2600 | 8 |
| Huge | 3850 | 12 |
| Vast | 7650 | 24 |

Budgets are provisional, derived from weighted fleets feasible under the former caps and rounded up to 50 SU. [Prices/calculation](SUPPORT_UNITS_TABLE_2026-10-28.md); active data: design/cataclysm.json. Existing Vaygr carrier limits are Normal 4 and Huge 5. The earlier proposed divisor 6 belonged to the abandoned carrier capacity bonus.

One squadron costs its configured full batch size multiplied by the per-hull price. The counter below Resource Units reports nominal owned batches, including docked units; it excludes production queues and does not measure surviving hulls in damaged squadrons. Native supply handles production admission; the HUD does not change ownership, production or caps.

## Display and localization

SU prices appear in the build list, normal/timed tooltips and selected-ship roles. The uppercase resource caption and gold three-person icon sit below RU; the duplicate cap-popup row is removed. Latin SU is used in all short prices. The four menu badges are Hiigaran, Vaygr, Taiidan and Kushan.

Six separate native UCS dictionaries each contain 443 matching compact IDs. Runtime display fields use ASCII $ID references. Russian Carrier/Carriers are Авианосец/Авианосцы. Approved Vaygr names are Разведчик, Ракетный корвет, Минный корвет, Абордажный фрегат and Стэлс-генератор. Five original Russian dictionaries receive only the 35 approved entry changes; their generated full copies stay outside Git. Other languages retain their original names.

## Implementation and review

Authoritative sources are tools/cataclysm.py, cataclysm_descriptions.py, tools/templates/cataclysm_*.lua and design/cataclysm.json. Ship configurations branch on getRulesNum(NewShipType, "hwmp_cataclysm", 0); ordinary fields/calls remain unchanged. Native supply is scaled by 32 into exact binary fractions; the visible HUD uses ordinary SU. Source checks cover both branches, all race/profile caps, 24 race/language build tables, both base-time settings, native Lua 4 parsing and complete extraction of all seven archives.

The review removes three obsolete locale Lua tables, retains exactly the active dictionary references, guards private ID ranges and native collisions, and replaces a dynamic import in Workshop staging. [Review and validation](CODE_REVIEW_2026-10-30.md).

```powershell
python tools/hwmp24.py --package --candidate
```

Candidate output is local/HWMPPatch245-candidate. The ordinary local/HWMPPatch24-release preserves 2.4.1. Preparation does not install, launch, publish or advance downstream pins. Workshop source staging uses --candidate and the existing item 3827773780, then an explicitly approved Toolkit update.

## Evidence and remaining field tests

The owner confirmed ordinary Steam startup, changing SU totals (64/1450 to 70/1450), build prices, the final resource-row layout and readable Russian localization. On 30 October the owner reported the latest local version appears to work and requested a public field test. Earlier Access Violation root cause remains unknown; it did not recur in accepted runs. [Development history](archive/2026-10-29/CATACLYSM_2_4_5_HISTORY.md) preserves rejected revisions separately.

Still open: actual weighted build thresholds and fractional enforcement; simultaneous queues/cancellation; damaged batches/replenishment; capture/crates; saves; ordinary→Cataclysm→ordinary mode switching in one process; two-client synchronization and full matches. Source checks, component harnesses and startup checks do not close those tests. If mode switching retains the wrong supply definitions, that is a functional defect requiring a fresh-process workaround or a code fix before claiming reliable mode switching.

Use identical Workshop archives on network peers. Toolkit repacks loose files, so its output must be downloaded and verified separately from the local developer BIGs. Publication status and exact native checks belong to the release receipt/review, not inferred from source composition.
