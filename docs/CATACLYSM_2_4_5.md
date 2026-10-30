# Cataclysm Support Units mode

[Русский](ru/CATACLYSM_2_4_5.md)

Choose **HWMP 2.4.5 Cataclysm** under Game Type in skirmish/multiplayer. The existing Hiigaran, Vaygr, Kushan and Taiidan races share a weighted SU budget. Ordinary HWMP modes remain available in the same package.

**Known defect: the native SU limiter does not enforce the displayed budget reliably.** Both early build refusal and paid construction beyond the displayed ceiling have been reproduced. This remains an experimental field test. [What fails and what is unverified](KNOWN_ISSUES.md).

## Current fleet rules

| Unit Cap | Nominal SU | Native ceiling (SU / 32) | Zero-SU probe cap per family |
|---|---:|---:|---:|
| Small (Low) | 1440 | 45 | 4 |
| Normal | 1920 | 60 | 6 |
| Large | 2560 | 80 | 8 |
| Huge | 3840 | 120 | 12 |
| Vast | 7680 | 240 | 24 |

The owner selected these multiples of32 on 30 October 2026. Previous budgets1450/1900/2600/3850/7650 changed by−10/+20/−40/−10/+30. Integral ceilings remove fractional budget values; ship-cost accounting remains defective. This update changes ceilings and HUD denominators only, not ship prices, combat statistics or the divisor32.

Carrier40SU; shipyard50SU; starting mothership0SU. Carriers add no capacity. Existing carrier/shipyard count caps, research slots, mothership limits and classic zero-SU probe caps remain. Layout supplies are unchanged. [All113 prices](SUPPORT_UNITS_PRICES.md).

An entry uses its full configured batch price. The counter below Resource Units sums currently owned entries, including docked ones; it excludes construction queues and does not measure the surviving physical hulls of damaged squadrons. Prices appear in construction, tooltips and selected-ship descriptions.

## Localization and use

Six native tooltip languages are supported: English, French, German, Italian, Spanish and Russian. Russian carrier and selected Vaygr ship names are corrected. The main menu has four original-race emblems. Use the same Workshop archives on every multiplayer peer; do not stack another Players Patch over this complete package.

Startup, readable prices/counter and Russian UI have human confirmation on the preceding runtime. Source and Lua4 checks cover the new ceilings; a new native run of this ceiling revision is not claimed. Full matches, two-client synchronization, saves with queued builds and simultaneous producers remain unverified.

## Implementation

`design/cataclysm.json` supplies prices/budgets; `tools/cataclysm.py` and templates generate the rules and HUD. Ship definitions branch on the Game Type property. Ordinary ship fields/calls are preserved. Generator validation requires integral ceilings below 250. The diagnostic harness is excluded from normal runtime. [Architecture](PATCH_ENGINEERING.md), [build/update](UPDATE_WORKFLOW.md), [historical investigations](archive/README.md).
