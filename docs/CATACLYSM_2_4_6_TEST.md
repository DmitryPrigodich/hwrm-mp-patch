# HWMP 2.4.6 Cataclysm Test1

> Reference only: SU is excluded from the current 2.4.6 candidate by owner decision on 2 November 2026. Published 2.4.5 and prior experiments are described below.

[Русский](ru/CATACLYSM_2_4_6_TEST.md)

An isolated, unpublished prototype requested on 31 October 2026. It is not the Workshop 2.4.5 release. Native launch, save/load and multiplayer acceptance have not been performed for this build. Package/source checks are not native validation.

## Rules to try

Choose **HWMP 2.4.6 Cataclysm Test1** in Game Type after installing the complete test package separately. The package includes the main BIG and six sibling language BIGs; the main archive alone has English fallback. Do not stack it over another complete Players Patch/HWMP. This preparation does not install or launch anything.

The Unit Cap size selector is hidden and fixed. Legacy Small/Normal/Large/Huge/Vast values resolve to identical rules. Ordinary game types retain their existing definitions.

| Race | Mothership grant | Shipyard grant (maximum 1) | Carrier grant / maximum | Maximum capacity |
|---|---:|---:|---:|---:|
| Hiigaran | 300 | 400 | 150 / 4 | 1300 |
| Vaygr | 300 | 400 | 100 / 6 | 1300 |
| Kushan | 300 | No new shipyard | 250 / 4 | 1300 |
| Taiidan | 300 | No new shipyard | 250 / 4 | 1300 |

Capacity comes from currently owned living suppliers, including docked entries. Supplier loss, retirement or transfer removes its contribution; capture adds it to the new owner. Any combination is clamped to 1300. No initial 300 is invented for starts without a mothership. The HUD shows nominal owned SU / current capacity, refreshed every 0.5 seconds.

Supplier prices remain: carrier 40 SU, shipyard 50, mothership 0. Capacity is a separate grant, available only after completion. A carrier still needs 40 free SU to start; its future bonus cannot pay its own construction. At the listed maximum supplier fleet, suppliers themselves consume 210 SU for Hiigarans, 290 for Vaygr and 160 for HW1 races. These are gross capacity limits, not 1300 free combat SU.

All requested price changes are in this candidate: HW1 controller 8, HW2 refinery 10, all collectors 2, HW1 repair/salvage corvettes 3/4, HW1 destroyer/missile destroyer 80, HW1 heavy cruiser 150, Vaygr heavy missile frigate 15. The package includes a complete candidate price table. Published 2.4.5 tables/data are unchanged. Zero-SU probes retain Normal native caps (6 per relevant probe family); carrier, shipyard, research and formation Layout caps remain separate.

## Experimental enforcement and limits

The defective fractional native SU weights are set to zero only in the Cataclysm branch of this package. A deterministic script iterates all players and ship types, recomputes integer owned cost/capacity and restricts types for which owned cost + new entry cost exceeds capacity. Equality is allowed. It releases only restrictions it claimed and preserves known stock game-rule restrictions. It does not grant research or change prerequisites, RU prices, combat stats or production times.

**This is not an atomic queue reservation system.** Already queued orders, several producers or rapid clicks between updates may still exceed capacity. The HUD excludes queues. Whether native restrictions pause existing orders or only prevent admission needs testing; an existing exact-fit queued order could also stall. No automatic cancellation/refund/destruction is added. Supplier loss may leave the existing fleet over capacity; new positive-cost entries are then blocked. Unrecognized external restriction writers and rewind/load behavior are not certified. Do not use this prototype to claim the old SU enforcement defect is solved.

## First native checks

1. Confirm the Test1 title and hidden Unit Cap selector. Start each race with the standard mothership fleet. Record the actual starting fleet and SU display; suppliers already present must add their bonus.
2. Build a carrier: capacity increases by 150/100/250, while owned cost increases by 40. Build a HW2 shipyard: capacity +400, owned cost +50. Build to the listed carrier limit and confirm the maximum is 1300. A further carrier must be blocked by its count cap.
3. Test a 15-SU entry with exactly 15 available, then 14, then 0. Wait at least one update after changing the fleet. Record button state, actual paid progress and completed entry, not queue presence alone.
4. With one entry's worth of free capacity, order from two producers; repeat by queuing multiple copies of the same type and by rapidly clicking. Record used/capacity before, during and after completion. Try pause/resume/cancel; report a stalled exact-fit order too.
5. Lose/retire a carrier. Capacity must fall; existing ships remain. Retire a combat entry and verify affected build options reopen. Capture/transfer a supplier and check both players, with a 1300 clamp.
6. Check zero-SU probe caps, research, docking and ordinary game types; then saves/loads and two clients with identical seven BIGs. These are pending native checks, not passes.

Logs emit `HWMP_SU246|player=...|used=...|capacity=...` when values change. `HWMP_SU246_ERROR` means required native API availability was not satisfied; the gate did not start. Preserve the build hash and report the action/expected/actual result.
