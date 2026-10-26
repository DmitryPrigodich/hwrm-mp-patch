# Gravity well save/load repair

[Русский](ru/GRAVITY_SAVELOAD_FIX.md)

The known active-well defect was reproduced and repaired for original Kushan/Taiidan generators. This is additional compatibility of the skirmish/MP base, not a certification of every campaign save. Negative historical runs remain negative.

## Root cause

Save two overlapping active fields, destroy the sources, load the checkpoint and destroy them again. The old base left targets at Move0/speed0 even though both generators physically disappeared and Destroy callbacks ran. Hiigaran/Vaygr targets were affected too. The file loaded; file corruption was not demonstrated.

Native traces showed world/SobGroup membership rewinding while ship custom-code effect tables could retain future mutations. A later callback resnapshotted an already-blocked state as its original baseline. Fixing the unrelated ScoutSpeedLimiter serialization ID removed Lua errors but did not repair this state mismatch.

The new journal stores original ability permissions/speed and owners in native SobGroup membership. Lua tables are caches. It creates no helper ships, uses no ScriptFlags and never globally enables movement. The loaded generator preserves its checkpoint previous-target group so a target leaving range before the first callback is still released. Empty/dead record markers cannot be decoded for a new target generation.

SCAR can change an allowed baseline through HWMP_SetAbilityAllowed/HWMP_SetSpeedAllowed while ship code owns a temporary lock. Direct external engine flag changes are not intercepted. The generated effects.lua is self-contained: an earlier cross-file wrapper experiment did not intercept the native calls. A Volume-based metadata replacement returned stale state/asserted and was rejected. No replacement scripts/save.lua is shipped.

## Exact native evidence before the release review

Negative old-base run: b8deead4d1abb85f0d82c3e8ae7312516584039ef75ebda295e8f442d86296a2, SaveLoadTrace2failed. Journal SHA256:50f43107508ee4e9b8683d0a0fd7ad63e1df0f7c8e670736abeab640e85ee24c.

Ordinary-code diagnostic run a4e54a0c0fb395be982caa530dd1faca03a831bb31c339836ab6dedada6a1065 inherited base fix d2376f7b… byte-for-byte, with only the declared diagnostic UI registration:

| World | Result | Native log SHA256 |
|---|---|---|
| JournalPressure |2passed|3fdfb6b381e989188eaad39ee5cca4291c75c29219d3a8b97f86f7fef18042bb|
| JournalRecycle |2passed|2e5003cf4ffc7175153a227f015304214fb576852b354e39e2883897e106552d|
| SaveLoadAuto |2passed|e6c473826ea37901578e1a9bd468e9497f57867640b127acd5de35ffee9636a9|
| SaveLoadCold |2passed|15609fc741b9483a09198fdae17741f7dc2a68b061eee405a8629f9e017825d0|
| SaveLoadCoop |2passed|e41e817924eaba9dcfa106f002b66d45fe2bfb8200b7e6fd8ec7eca601f7b9bb|
| SaveLoadEmpty |2passed|b4485d74c41b7a6053fe1fdd289c0117cab70dd847f84db4abbe1d73b7a0f059|

Auto/Cold confirm actual rollback, overlapping locks, Hgn range exit, sequential source destruction and real post-release movement around1783m. Cold uses a new process without a prior ship cache. Empty rolls back before activation and a future-only source, then tests a new activation. Coop preserves a scenario's Move0/speed0.625 while released Hgn/Vgr controls move. Recycle destroys all old anchors, spawns a fresh source/target and verifies another lock/release cycle.

The compact targeted candidate433a9826… additionally passed Transport6/6 and Salvage6/6+6/6 with original Scuttle1/0. Earlier GravityToggle/Expiry8/8 remain separate no-load results. New release-review checks are recorded in CODE_REVIEW_2026-10-26.md rather than being silently attributed to these old hashes.

## Performance

Same pressure setup:200configured target entries,6generators, roughly game t6→26.25. These are individual external monotonic wall-time samples, not FPS or pure CPU.

| Variant | Wall seconds | Relative to old control |
|---|---:|---:|
| Old base without journal, c7f1485b… |20.093|1.00×|
| Functional fixed64-bit prototype,83ec3239… |59.860|2.98×, rejected|
| Compact owners/numbers,3f5ff221… |22.500|1.12×|
| Targeted owner release,433a9826… |21.328|1.06×|
| Ordinary code with live-marker check,a4e54a0c… |21.938|1.09×|

Initial t0→6 samples were6.641/7.047/6.250s for old/candidate/ordinary code. The variability does not establish the exact cost of one final safety check. The first ordinary pressure mechanics passed, but its external timer read a preceding suite:end and was rejected; the repeat filters mode and preceding-log SHA.

## Compatibility and handoff

New checkpoints contain the journal. Old active-well saves made before it may lack original baseline data and cannot be guaranteed. Saved capture/transport/missile states and all campaign transitions are not certified by these worlds.

The repaired pre-review ordinary archive was4bfa821379762964cbf637294783c79428c1b9a4bc181df1b7ec18951cb2d091,105157768bytes,fix d2376f7b5526bbc0ae57255e1feabc2ecfdcd0137dcb328f7d51a963982a54d5,39overrides/1124sourcefiles. The later publication review adds six-language overlays, packaging/readability improvements and a new release identity; see its report. It does not change approved combat/economy numbers.

Consumer pins/builds remain separate. The author reopened single-player use of future new-race holding on26October; it now needs its own design/integration tests rather than a categorical campaign ban. [Field acceptance](CLOSURE_CHECKLIST.md).
