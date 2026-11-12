# HWMP Patch 2.4.6 — candidate

[Русский](README.ru.md)

A standalone Homeworld Remastered patch for the original four races, based on Players Patch 2.3 Test build 21.

**This 2.4.6 candidate removes Support Units.** The published 2.4.5 limiter failed native accounting tests; the separate 2.4.6 experiment does not reserve build queues reliably. The candidate restores classic unit caps and removes the Cataclysm selector, SU counter and SU prices. Other improvements remain.

## What remains

- Gravity-well ability and speed restoration, with specific tested save/load cases.
- Support-frigate cargo recovery, capture/self-destruct permissions and independent stalled-docking timers.
- Taiidan missile-defense targeting, the Vaygr Medium missile binding and two scoped missile corrections.
- Six-collector Hiigaran/Vaygr starts and the approved Assault Frigate final speed-accuracy multiplier of 1.2.
- Build/research timing tooltips in six languages; Russian ship-name corrections, four race emblems and menu music.

The candidate is prepared locally. [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) still contains **2.4.5 with its known SU defect** until an explicitly requested update. Use one complete patch and matching archives on every multiplayer client. Full-match and two-client acceptance remain pending; see [known issues](docs/KNOWN_ISSUES.md).

## Development

Requires your own game, Toolkit and pinned Test21 inputs. Code-only checks need no game assets:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

For a separate candidate:

```powershell
python tools/prepare_inputs.py
python tools/hwmp24.py --package --candidate
python tools/install_hwmp24.py --candidate
```

The last command prints an installation plan. `--install` applies it only when explicitly requested. Candidate output is `local/HWMPPatch246-candidate`; the ordinary build uses `local/HWMPPatch246-release`. Their sources and receipts are isolated; earlier releases are preserved. Python `-O`/`-OO` and `PYTHONOPTIMIZE` are rejected before tool work.

[Documentation](docs/README.md) · [Update procedure](docs/UPDATE_WORKFLOW.md) · [Local installation](docs/LOCAL_INSTALLATION.md) · [Review changes](docs/REVIEW_2_4_6.md) · [History](docs/archive/README.md).

Dependency direction: base → HW1 races → campaign. Consumer pins/builds are never advanced automatically. On Windows, `git config core.longpaths true` may be needed before cloning into a long path.

Credits: Players Patch 2.3 team; 2.3Test: Fear/Novaras; HWMP: AmDDRed, Hix, Twofoxich. [Full credits](docs/CREDITS.md), [maps](docs/MAP_CREDITS.md). Game assets, BIGs, local caches and personal logs are excluded from Git.
