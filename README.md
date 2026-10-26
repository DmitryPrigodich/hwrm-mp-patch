# HWMP Patch 2.4

[Русский](README.ru.md)

A standalone Homeworld Remastered patch built on **Players Patch 2.3Test build21**. It preserves the original four races and their HW2-style progression while fixing shared mechanics. **Field-test candidate:** automated engine checks cover specific cases; real multiplayer acceptance is still required.

## Changes

- Original Kushan/Taiidan gravity wells release overlapping locks correctly, including tested save/load cases. Previous ability restrictions and speed are preserved.
- Support-frigate transports return surviving passengers; salvage preserves each ship's original self-destruct permission; stalled docking uses independent ship-ID timers.
- Taiidan defense fighters refresh missile selections when targets change without changing their count. The missing Vaygr Medium missile weapon-fire binding is restored.
- Narrow accepted balance changes: **6 Hiigaran / 6 Vaygr starting collectors**, and the Assault Frigate's last speed-accuracy node **4 → 1.2** on its three cannons. Two inherited missile inconsistencies are corrected; no broad rebalance is claimed.
- Build/research tooltips use effective base times and the selected native language. English is the documentation/default starter language; French, German, Italian, Spanish and Russian tooltip overlays are included.
- Front-end identity: native HW2 planetary backdrop, a row of Hiigaran/Vaygr/Taiidan badges, HWMP 2.4 footer and the requested **Inhibitors** menu track. [Details](docs/MENU_BRANDING.md).

## Field tests still needed

1. Two real multiplayer clients using identical release archives: synchronization, overlapping wells, transport, capture, docking and missile defense.
2. Normal and 2x starts from the standard UI; six collectors per side; build/research screens in each supported language.
3. Visible squadron losses and repair/replenishment. A script entry count is not a physical hull count.
4. Paid UI hyperspace, charging cancellation and actual return to Guard after missile interception.
5. Full Hiigaran ↔ Vaygr matches on varied maps, with side swaps, raids and late fleets.

Record the archive hashes and reproduction steps. [Acceptance checklist](docs/CLOSURE_CHECKLIST.md) · [Engine results](docs/AUTO_TEST_RESULTS.md).

## Build and use

Requires your own game, Toolkit and the pinned Test21 input; no game assets are stored here.

```powershell
python -m pip install -r requirements.txt
python tools/prepare_inputs.py
python tools/hwmp24.py --package
python tools/install_hwmp24.py --install
```

Output: `local/HWMPPatch24-release`. Direct starter: `HWMP Patch 2.4.cmd` (English); add `-Language Russian` or another supported language. For the native launcher's single local slot, use the reversible [slot selector](docs/LOCAL_INSTALLATION.md). Published on [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) as **HWMP Patch 2.4 - Field Test**. For multiplayer acceptance, every client should use the same Workshop version; Toolkit archives have different hashes from the local development build.

Use this complete package by itself; do not stack another Players Patch on top. Old active-well saves made before the new journal are not guaranteed to resume correctly. New checkpoint tests do not certify every campaign or level transition.

## Development

[Architecture and changes](docs/PATCH_ENGINEERING.md) · [Update/release procedure](docs/UPDATE_WORKFLOW.md) · [Localization](docs/LOCALIZATION.md) · [Workshop preparation](docs/WORKSHOP.md) · [Frozen test examples](examples/native-testgrounds/README.md).

Dependency direction: **hwrm-mp-patch → hwrm-hw1-races-reimogined → hwvr-to-hwrm-mod**. Building this base never updates consumer pins, builds or installations.

Credits: Players Patch 2.3 team; 2.3Test: Fear/Novaras; HWMP 2.4: AmDDRed, Hix, Twofoxich. [Full credits and map authors](docs/CREDITS.md). [Players Patch](https://steamcommunity.com/sharedfiles/filedetails/?id=1190476337) · [2.3Test](https://steamcommunity.com/sharedfiles/filedetails/?id=1413859511) · [upstream code](https://github.com/Novaras/2.3-Test). This repository publishes code and documentation, not models, media, compiled BIGs, caches, personal logs or saves.
