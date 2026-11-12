# HWMP 2.4.6 backlog — Cataclysm redesign

> Reference only: SU is excluded from the current 2.4.6 candidate by owner decision on 2 November 2026. Published 2.4.5 and prior experiments are described below.

[Русский](ru/BACKLOG_2_4_6.md)

Owner request, 30 October 2026. On 31 October the owner authorized a separate test BIG; [Test1 is prepared](CATACLYSM_2_4_6_TEST.md), without native acceptance, installation or publication. This is a future-version plan, not current 2.4.5 behavior. [Current SU prices](SUPPORT_UNITS_PRICES.md).

## SU price changes

All values are per hull. HW1 covers original Kushan/Taiidan, HW2 covers Hiigaran/Vaygr. New races in the sibling repository are outside this request.

| Ship | Applies to | Current | Planned |
|---|---|---:|---:|
| Resource Controller | HW1 | 10 | 8 |
| Mobile Refinery | HW2 | 13 | 10 |
| Resource Collector | HW2 | 4 | 2 |
| Resource Collector | HW1 | 3 | 2 |
| Repair Corvette | HW1 | 3 | 3 |
| Salvage Corvette | HW1 | 4 | 4 |
| Missile Destroyer | HW1 | 45 | 80 |
| Destroyer | HW1 | 40 | 80 |
| Heavy Cruiser | HW1 | 90 | 150 |
| Heavy Missile Frigate | Vaygr (HW2) | 12 | 15 |

Repair/Salvage Corvette prices are reconfirmed, unchanged. When implemented, synchronize authoritative data, generation, SU labels/descriptions, EN/RU tables and checks.

## Capacity redesign

- Mothership supplies the initial **300 SU**.
- Shipyard supplies an additional **400 SU**.
- Each carrier supplies **150 SU** for Hiigarans, **100 SU** for Vaygr, **250 SU** for Taiidan/Kushan.
- Target: the same maximum **1300 SU** for all four races.
- Fixed Cataclysm rule, without Low / Default / Huge or other Unit Cap size selection. Preserve ordinary modes.
- Retain carrier count limits; reconcile their values with the new formula.

Capacity granted and a ship's own SU price are separate. This request does not specify new mothership/shipyard/carrier prices; do not silently remove current prices.

## Resolve and validate when work resumes

- Reconcile ship count limits and the 1300 target. HW2 arithmetic: Hiigaran 300 + 400 + 4 × 150 = 1300; Vaygr 300 + 400 + 6 × 100 = 1300. These are required counts for that formula, not assertions about current caps.
- HW1 without a separate shipyard: 300 + 4 × 250 = 1300. Granting them a further 400 leaves 600, which is not divisible by 250. The owner has not selected a resolution; do not invent a shipyard or another bonus.
- Define supplier destruction/capture/transfer/retirement, exceeding reduced capacity, alternate starting fleets and multiple shipyards/motherships. The 1300 maximum is requested; its enforcement mechanism is undecided.
- Existing native weighted accounting remains defective. New prices and capacity rules alone do not repair it. Design and test exact fit, a 1-SU shortage, multiple producers, queue reservations/cancel/pause, docking, capture, save/load and two-client synchronization.
- Before release: review bugs/regressions, Lua 4, performance, readability and maintainability; appropriate checks and separately authorized native tests. Installation and Workshop publication require an owner request.

Recommended implementation effort: **High**, for dynamic capacity and native-accounting validation. Routine backlog maintenance: **Medium**. No application setting changed.
