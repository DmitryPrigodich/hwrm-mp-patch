# Native automatic test grounds

[Русский — detailed original notes](ru/AUTO_TESTS.md)

HWMPAutoTests is an isolated Extra Missions package built from the complete prepared base. Normal gameplay files must match that base byte-for-byte. Its only declared base exception is UISettings registration for an otherwise inactive owned auto-load screen. The ordinary mod does not contain that screen.

```powershell
python tools/auto_testgrounds.py
python tools/auto_testgrounds.py --install
python tools/run_auto_queue.py JournalRecycle SaveLoadEmpty SaveLoadAuto SaveLoadCold SaveLoadCoop
python tools/run_auto_pressure.py
python tools/analyze_auto_tests.py
```

Installation/launch needs an explicit human request. Never rebuild/reinstall during a queue with future launches. Each native process is identified by its own PID, executable and HWMPAutoTests command. Terminal runs are collected/closed by the runner; a healthy timeout stays open. No unrelated game is stopped. Invalid pilots remain preserved as invalid rather than being relabeled passed.

## Reusable worlds

- Mechanics/GravityScope/GravityToggle/GravityExpiry: baseline permissions, overlaps, four target races, repeated sources and natural completion.
- SaveLoadAuto/Trace: save under real fields, mutate the future world, load the owned checkpoint, confirm rollback and release. Cold starts a fresh process; Empty saves before activation and before a future generator exists; Coop changes allowed baseline from SCAR while ship VM owns the lock.
- JournalRecycle: destroy every old anchor, create a fresh source/target and check another cycle. JournalPressure:200 configured target entries under6sources, with mixed flags/speed and physical movement after release.
- Transport/Salvage/SalvageBaselines/DockStall: native off-map cargo/return/source destruction, capture interruptions, original Scuttle0/1 and forced stall under real fire with order controls.
- Defense/DefenseIdentity/DefenseOrders/DefenseIntercept: native missile filters/target replacement, explicit orders and actual guarded targets. An explicit order is not an automatic Guard-return test.
- Progression/ResearchEffects/HW1Damage/PaidProduction: prerequisites/queue, actual HP/speed, paid HW1 damage tiers with foreign-race controls and paid old/new carrier builds.
- Economy6/7/Matrix/Raids/Recovery: clean income and scripted/real receiver pressure. Mines/CombatGeometry/Antistrike/SpeedCurve: scoped combat measurements with explicit setup controls.

Private diagnostic ship/weapon transformations and hashes are recorded in local source metadata. Normal definitions are not overwritten by those private types. Geometry with Attack can move a ship even if AB_Move=0; stationary fixtures additionally set speed0. Missile target loss disables new fire and uses separate destruction-damage controls.

## Evidence rules

The loader stages only `player:Campaign/HWMPAUTOTESTS/HWMPAutoCheckpoint.sav`, owned by the current run. It checks a fresh save label/hash and allowed internal research IDs; prior owned copies are preserved. A request to LoadGame alone is not success: require time/marker rollback and OnStartOrLoad. Cold must load the same run's checkpoint in a new process.

Gravity results require remaining-owner lock, correct range-exit release, original flags/speed, real generator removal and meaningful movement. Source mocks and Lua4 parsing complement these tests; neither is a native pass. SobGroup_Count is never reported as a physical hull count.

The pressure instrument filters run/mode and the preceding log SHA. It measures an external monotonic wall-time interval, not FPS or pure CPU. Do not mix repeated samples, game time and process launch delay. A stale previous suite:end invalidates the timing sample even if the native mechanics later pass.

Raw logs, checkpoints, process commands and environment metadata stay in ignored local/auto-tests. Public records contain methods, result summaries and log hashes only. [Results](AUTO_TEST_RESULTS.md), [gravity repair](GRAVITY_SAVELOAD_FIX.md), [field remainder](CLOSURE_CHECKLIST.md).

Frozen examples are preserved under examples/native-testgrounds. That directory is not a runtime source or automatic build input.
