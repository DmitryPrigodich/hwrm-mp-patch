# Support Units feasibility — 27 October 2026

[Full Russian investigation](ru/SUPPORT_UNITS_RESEARCH.md)

**Assessment:** a shared weighted fleet budget is a credible HWRM mod design. Native supply families are the strongest implementation candidate; an informational script counter is a separate, less intrusive route. Neither has been tested in the engine in this investigation. Dynamic capacity supplied by carriers/modules remains unresolved.

This is research for **HWMP 2.4.1**, not a gameplay change. No package, installation, launch, Workshop update or downstream dependency change occurred. Runtime ownership is `hwrm-mp-patch`; future race-specific definitions belong to HW1 Nova Races. Somtaaw/Beast entries in the sketch do not authorize adding these races to HWMP.

## Evidence and artifacts

- The owner's 101-row sketch is transcribed in [research/support-units/sketch.json](../../../research/support-units/sketch.json). On 27 October the owner confirmed `2|14 = 2 SU per ship × 7 ships per full group`. Partial-loss accounting is undecided. Candidate stock identifiers are explicitly provisional; absent prices are unknown, not zero.
- [tools/audit_support_units.py](../../../tools/audit_support_units.py) passively inspects effective stock/Test21/HWMP overrides. The initial run covers 126 ship types mentioned in four build tables and hashes 142 inputs. Build-table inclusion does not establish legal MP availability: special/blocked entries and managed drones are included. Source defaults do not establish visible hull counts.
- Local output: `local/support-units-research/audit.json` and `catalog.md`. No assets are copied. Run `python tools/audit_support_units.py` with configured native inputs and existing requirements; optional `--output` changes only the report destination.
- Examined owner commit: `e7faaa03af3a9e3bafd16d24a9c22aea7623b31b`; fix revision `918818ee91a81a3c46bfa61b8a301649716ec16868f0a9b4da7ac2e8bb5970b7`.

## Findings

HWRM supports multiple, weighted, fractional supply assignments. Native definitions demonstrate a seven-craft Vaygr interceptor batch costing five Fighter supply; native `unitcapsFamily`, `supplyLimit`, `supplyShow` and `UnitCapInfoPopup` provide a plausible common-budget/display route. [HWRM 2.0 modding discussion](https://web.archive.org/web/20220720015354/https://forums.gearboxsoftware.com/t/hwr-2-0-modding-changes/1501768), [setSupplyValue](https://github.com/HWRM/KarosGraveyard/wiki/Function%3B-setSupplyValue), [supplyLimit](https://github.com/HWRM/KarosGraveyard/wiki/Function%3B-supplyLimit).

The [original HWC manual, printed pp. 42 and 47](https://homeworldarchives.com/media/Homeworld-Manual-Cataclysm.pdf) describes active SU, queued reservations, free capacity, support modules/carriers and capacity-aware salvage/infection. Reproducing that whole system is more work than adding one fleet score.

Native partial-loss/replenishment behavior, queue reservation across producers, ownership changes and custom-family upper limits require engine tests. A [2016 mod author's report](https://steamcommunity.com/sharedfiles/filedetails/?id=485998120) mentions an effective 250 cap; it does not prove the same ceiling for a new weighted family in the current engine. Fractions may permit scaling, but native integer UI formatting then requires a separate display solution.

## Recommended sequence

1. Calibrate one native batch, a single ship and losses/Dock against both the native cap and `Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping`. Avoid treating squadron counts as physical hull counts.
2. Start with an informational, labelled nominal-group SU counter; preserve existing class limits. Recompute from current ownership rather than maintaining fragile build/death totals. Price every relevant type or visibly mark the count incomplete. Show only the local player's own fleet by default.
3. Test a separate experimental mode with one shared native family and a fixed budget. Keep ordinary modes unchanged. Remove/relax old combat class/subclass limits deliberately; hiding them does not disable them. Keep formation Layout supply and unique-asset constraints separate.
4. Balance Hgn/Vgr first. Study economy, utility stacking and mono-fleet extremes before choosing a total. Do not transfer the sketch's custom Taiidan roles/prices onto stock ships automatically.
5. Investigate carrier/module capacity only after the fixed-budget experiment. `addedUnitCaps=101` in old definitions does not demonstrate working HWC-style supply provision.

**Effort:** High for a native experiment and interpreting its results; Medium for transcription, reporting and established follow-through. Extra High is reserved for a demonstrated engine/synchronization obstacle.
