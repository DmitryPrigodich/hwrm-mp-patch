# Local installation

[Русский](ru/LOCAL_INSTALLATION.md)

The candidate is separate from installed mods and the still-published Workshop 2.4.5.

```powershell
python tools/hwmp24.py --package --candidate
python tools/install_hwmp24.py --candidate
```

The second command is a read-only plan. Add `--install` only on the owner's request, with game/launcher closed. The installer verifies its selected package's portable receipt, file inventory and hashes, preserves the previous owned installation and refuses unknown files/links. It does not stop or launch the game. Omitting `--candidate` selects the independent ordinary 2.4.6 package.

Installation owns only `HomeworldRM/DataWorkshopMODs/HWMPPatch24`; original BananaDLC and other mods remain guarded. The native launcher has one local slot; changing it is a separate reversible operation with its own backup. `HWMP Patch 2.4.cmd` is the existing direct starter (technical name retained); `-Language Russian` selects Russian and `-PrintOnly` prints the launch command. Running it explicitly opens the normal menu.

For an explicitly requested launcher-slot switch, `launcher_slot.py hwmp --candidate` prints a plan; add `--apply` to select it. `launcher_slot.py previous --apply` restores the preserved previous slot. Never fabricate numeric subscription IDs or overwrite a running game's files. [Complete workflow](UPDATE_WORKFLOW.md).
