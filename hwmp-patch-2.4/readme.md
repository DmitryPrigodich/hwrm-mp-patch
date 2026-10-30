# HWMP Patch 2.4.5 — Cataclysm

[Русский](readme.ru.md)

A standalone Homeworld Remastered multiplayer patch based on **Players Patch 2.3Test build21**, retaining the original four races. [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780). Use the complete package by itself and the same Workshop revision on every MP client.

**Cataclysm is an experimental field test with a known SU-limiter defect:** build refusal can occur early and some compositions can exceed the displayed budget. [Known issues](../docs/KNOWN_ISSUES.md). This update rounds ceilings; it does not repair fractional ship-cost accounting.

## Cataclysm

Select **HWMP 2.4.5 Cataclysm** under Game Type. Nominal budgets: Small 1440, Normal 1920, Large 2560, Huge 3840, Vast 7680. Existing carrier/shipyard and zero-SU probe count caps remain; carriers add no capacity. SU prices appear in construction/tooltips/selection, with owned-fleet totals below RU. Queued construction is excluded from the HUD. [Rules](../docs/CATACLYSM_2_4_5.md) · [Prices](../docs/SUPPORT_UNITS_PRICES.md).

## Shared fixes

- Owner-safe gravity-well ability/speed restoration, including specific tested new save/load cases.
- Support-frigate cargo recovery, per-ship capture/self-destruct permissions and independent stalled-docking timers.
- Refreshed Taiidan missile-defense targeting and restored Vaygr Medium missile weapon-fire binding.
- Accepted Hiigaran/Vaygr6/6 collector starts, Assault Frigate final speed-accuracy multiplier1.2 and two scoped missile corrections.
- Native-language build/research timing tooltips in English, French, German, Italian, Spanish and Russian; four original-race menu badges and Inhibitors music.

Startup/UI and selected native mechanics have been checked; full-match balance and two-client synchronization remain unverified. Old active-well saves predating the journal are not guaranteed. [Field checklist](../docs/CLOSURE_CHECKLIST.md).

## Build and development

Requires your own game, Toolkit and pinned Test21 inputs. Game assets are excluded from Git.

```powershell
python -m pip install -r requirements.txt
python tools/prepare_inputs.py
python tools/hwmp24.py --package --candidate
```

Output: local/HWMPPatch245-candidate. The old2.4.1 release is preserved separately. [Local installation](../docs/LOCAL_INSTALLATION.md) · [Documentation](../docs/README.md) · [Update procedure](../docs/UPDATE_WORKFLOW.md) · [Functional data](../docs/DATA_FORMATS.md) · [History](../docs/archive/README.md).

Dependency direction: hwrm-mp-patch → hwrm-hw1-races-reimogined → hwvr-to-hwrm-mod. No automatic downstream builds or pin updates.

Credits: Players Patch 2.3 team; 2.3Test: Fear/Novaras; HWMP: AmDDRed, Hix, Twofoxich. [Full credits](../docs/CREDITS.md), [maps](../docs/MAP_CREDITS.md). Code/docs only: no models, media, BIGs, caches, personal logs or saves.
