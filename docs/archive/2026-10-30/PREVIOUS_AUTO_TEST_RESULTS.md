# Native results and limits

[Русский — detailed historical record](ru/AUTO_TEST_RESULTS.md)

This is a summary of completed26October2026 engineering work. Measurements, derived invariants and actual match acceptance are different categories. Earlier failed/invalid pilots remain in the detailed records and must not be counted as passes.

## Fixes accepted into the base

| Area | Native result | Practical boundary |
|---|---|---|
| Transport | 6/6 scoped cases | Scripted Dock/off-map/exit and both source destruction paths; not UI paid-charge cancellation. |
| Capture | 6/6 plus6/6 with original Scuttle0 | Identity survives capture/group changes; original0/1 restored. Unknown cold-tow baseline is not guessed. |
| Forced Dock |10measurements,10derived invariants | Real incoming fire, independent hull timers and order controls. Visible squadron repair remains separate. |
| HW2 research effects |4/4 | Real HP/speed on old/new stock ships and proper class/family scope; not every technology. |
| Paid production |4/4 | Hgn/Vgr Interceptor450RU, about35s before and27s after upgrade on old/new carriers, with controls. |
| Gravity without loads |Toggle8/8 andExpiry8/8 | Repeated overlapping fresh sources, natural finish and release in their fixtures. |
| HW1 damage tiers |18measurements plus18derived invariants | Paid upgrades with private constant weapon and foreign-race controls. Invalid structural-transform pilot excluded. |
| Income under real shots |6measurements | Receiver recovery observed on both sides; no universal harvest helper/rewrite justified. |
| Mines |8measurements | Positive sweeper/Assault controls; not a claim that every forced mine attack is useful. |
| Combat geometry |36measurements plus36setup invariants | Range/height/pursuit/turning; final stationary setup uses speed0. Earlier AB_Move-only setup is not a fixed-source control. |
| Native save/load repair |Auto/Cold/Empty/Coop/Recycle/Pressure2/2 each | Baseline journal, range exit, real movement, scenario prohibitions and fresh processes. Details and exact evidence hashes in GRAVITY_SAVELOAD_FIX.md. |

Missile defense includes a same-count target-replacement trace against a negative upstream control. Continuous Guard never left its order; actual automatic return after interception still needs field evidence. Missile cohort tests describe their specific launch/target geometry, not every individual missile in arbitrary battles.

## Accepted numerical policy

Clean600s economics in three receiver geometries gave Vgr/Hgn total-income ratios **0.974/0.991/1.014 at6/6**, versus **1.132/1.116/1.154 at6/7**. The author accepted6/6 for now. Collector internals and other economic coefficients were not changed.

The author accepted only the Assault's final speed node535/4→535/1.2 on3cannons, supported by48antistrike and60isolated speed measurements plus the applied normal ship. These are geometry-specific observations, not universal DPS or proof of full-match balance. Flak/platform/sweeper roles remain unchanged pending players.

## Save/load and performance

The old base reproduced2failed active-gravity loads despite real generator removal and stable callbacks. The file loaded; baseline state in ship custom-code could retain future mutations. The new native-group journal repairs the tested path and preserves restrictions rather than globally enabling all abilities.

The first functional fixed64-bit journal took roughly3× the pressure-control wall time and was rejected. Compact owners/numbers and targeted release yielded individual6–9% overhead samples for200configured targets/six wells. This is not FPS, not pure CPU and not a two-client benchmark. Long real matches still matter.

Old active-well saves from before the journal are not guaranteed. Every campaign/transition or saved transport/capture state is not certified by these worlds. The26October review adds localization/packaging checks; its final archive hashes and smoke results are recorded in CODE_REVIEW_2026-10-26.md.

## What remains

Only the explicitly listed field acceptance is currently queued: two real MP peers, ordinary/2x menus, visible hull repair, UI hyperspace/cancel/guard and full Hgn↔Vgr games. [Checklist](CLOSURE_CHECKLIST.md). Consumer race/campaign integration, their pins and Workshop publication are separate explicit steps.
