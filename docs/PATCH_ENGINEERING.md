# Patch architecture and engineering changes

[Русский](ru/PATCH_ENGINEERING.md)

The repository composes pinned Test21 data with scoped overrides. It does not try to recreate the entire game or make every race follow the same design. HW2 progression is the balance reference for the consumer race layer.

## Runtime boundaries

| Area | Implementation | Reason and constraint |
|---|---|---|
| Temporary ship effects | generated scripts/hwmp24/effects.lua | Each ship/squadron entry has its own original permission/speed plus a set of effect owners. Releasing one owner cannot release another. |
| Native checkpoint journal | tools/templates/effect_journal.lua | Native SobGroup membership rewinds with the world; ship custom-code tables may retain post-save changes. Tables are caches, not authoritative save data. |
| Gravity callbacks | playerspatch/ships_util/lib/gravwells.lua | Save-safe previous target set, owner-scoped release on exit/finish/destruction and fast reassertion of unchanged locks. |
| Transport | scripts/hwmp24/transport.lua | Preserve visibility and recover surviving off-map cargo on both support-frigate destruction paths. Redock progress cannot indefinitely hold release. |
| Capture | SobGroup_NoSalvageScuttle plus ID forwarding | Native Dock can already report Scuttle=0. Keep the earlier idle permission by stable ship ID; do not guess an unknown cold-tow baseline. |
| Dock recovery | ship-ID timer,11 forwarded callbacks | Separate stalled ships; preserve the3s threshold/5s retry interval and stop retrying when orders change. |
| Missile defense | tai_defensefighter callbacks | Refresh at the existing1.25s cadence; equal missile counts do not mean equal targets. Preserve owner/range filters and remembered Guard. |
| Localization/timing | production_data.py and language_data.py | Effective base times, native language strings, explicit fallback IDs and unknown/empty-description handling. |

## Journal format and performance

HWJB functions implement native membership storage; HWJC functions encode compact values/owners; HWJ functions manage checkpoint records and caches; HWMP functions are the public effect API. Group names under HWMP_JC_, HWMP_Journal2_ and HWMP_J2_O are reserved.

The header stores maximum record serial, revision and format marker. A record stores ability IDs with baseline0/1, optional original speed, a shared owner list and24-bit owner masks. Common numeric values use integer/fixed1/256 storage; other normal values use a full-width representation. Owner labels use compact known prefixes or a byte-preserving fallback. Do not change this format under the same namespace without a migration decision.

Metadata is encoded in membership of existing targets. No helper ships are spawned and no ScriptFlags are commandeered. Empty/dead target markers are rejected before decoding, allowing a later cycle after all previous anchors die. Serial/revision checks rebuild the cache; a same-counter branch can also recover entries missing from the cache. Record reads refresh data before releasing a native owner marker.

The expensive first prototype repeated64-bit data and owner strings. The accepted implementation shares owner lists, uses variable-width numbers, avoids writing unchanged records, reasserts known gravity locks without resnapshotting them and releases only targets carrying that owner's marker. A full scan of historical serial slots still exists on synchronization; long matches and two-client performance remain field-test items. Do not replace it with a stale Lua-only index without preserving rollback behavior.

Public cooperation: `HWMP_SetAbilityAllowed(group, ability, allowed)` and `HWMP_SetSpeedAllowed(group, speed)` update the desired baseline during a lock. Direct external engine flag changes are not automatically tracked. `HWMP_RegisterGravityTarget(ship_type)` extends the gravity target list. Validate campaign usage in its own context.

## Scoped numerical changes

- Standard and2x Vaygr00 starts:7→6 collectors, matching Hiigaran6. Carrier/full-fleet starts already have6; empty starts remain empty.
- Vaygr Assault Frigate: only the final speed-accuracy pair535/4→535/1.2 on three cannons. Other damage/range/falloff/cadence calls are preserved.
- Missile platform right launcher:6000→5500 range. Conflicting early SuperUtilityArmour0.8 entry removed while retaining0.85. The missing Medium missile WF is a resource binding fix.

Small lab samples did not justify new Flak, platform, sweeper or economy coefficients. Paid production, research effects, geometry and repeated income disruption were measured; complete match balance is still a human question.

## Validation and limits

Source mocks test ownership, mixed flags, cooperative updates, cache holes, extinction, transport/capture/Dock and language handling. Lua4 parsing checks native syntax. Full archive extraction proves composition. Native worlds prove their stated scenario only. See AUTO_TEST_RESULTS.md and GRAVITY_SAVELOAD_FIX.md; frozen code is under examples/native-testgrounds and is never imported into normal gameplay.

Old saves made with active fields before the journal may lack baseline data. The repair does not infer it by globally enabling movement or resetting every speed. New checkpoint tests passed warm/cold/empty/cooperative cases and physical movement after release; they do not certify all campaign transitions or saved capture/transport states.

The earlier consumer decision to forbid strikecraft holding in every campaign was a workaround for the old save defect. On26October the author reopened campaign use after this repair. The race layer may now design/research that ability for single-player too, subject to its own gameplay and native campaign validation. No race definition, research tree or consumer pin is changed here.
