# Cataclysm SU table and mode plan — 28 October 2026

[Russian implementation explanation and complete ship table](ru/SUPPORT_UNITS_TABLE_2026-10-28.md).

The owner's latest decision supersedes the growing-capacity variant: **fixed shared SU budget, original race/profile Carrier count cap preserved, no carrier capacity bonus**. Accepted costs are carrier **40 SU**, shipyard **50 SU**, starting mothership **0 SU**. Other draft prices retain their earlier status.

A carrier consumes both 40 SU and one Carrier slot. Spare SU cannot bypass the separate Carrier limit. The former Vaygr bonus divisor 6 is not a new count cap; actual ordinary Normal/Huge limits remain 4/5. The earlier fixed-Normal 50% bonus design remains archived research and is disabled in the basic mode.

The integer reference fleets were recalculated under all simultaneous old supply constraints at the new prices. Source Layout and banned internal/SP types are excluded. Common proposed budgets use the greatest race result rounded upward to 50:

| Profile | Common proposed SU |
|---|---:|
| Low / Small | 1450 |
| Normal | 1900 |
| Large | 2600 |
| Huge | 3850 |
| Vast | 7650 |

Normal changes from 1850 to 1900 because carriers now cost 40. These are draft calibration ceilings, not combat-tested balance. The workbook retains 113 ordinary/starting types, the 101-row original sketch, source caps and 332 reference rows. Editing prices recalculates the same reference fleets; reoptimize to obtain maxima at arbitrary new prices.

Implementation is planned as another Game Type in the existing HWMP package using existing races/ship IDs. Ordinary modes keep their prior caps. Cataclysm selects its own fixed weighted supply profile, releases ordinary combat class/subclass restrictions and retains Carrier plus deliberate unique-asset constraints. Production must meet both SU and retained limits, with existing RU/research/producer requirements. Native registration, static-load isolation, queues, partial-group replenishment, ownership, saves and two-client synchronization need an isolated prototype before release. No future version number is assigned here.

All 20 weighted totals, profile-dependent Carrier limits, zero carriers and disabled bonuses were verified. Unrelated source sheets and reference quantities were preserved. No native Excel/game launch, runtime/BIG edit, installation, publication or consumer pin change occurred. Recommended effort: Medium for table/document follow-through; High for the native prototype.

[Proposal snapshot and source hashes](../../../research/support-units/proposal-20261028.json).
