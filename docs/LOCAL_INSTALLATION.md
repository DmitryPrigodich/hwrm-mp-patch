# Local installation and native launcher

[Русский](ru/LOCAL_INSTALLATION.md)

Build and installation are separate. Close the game/launcher yourself before updating; no installer stops them.

```powershell
python tools/hwmp24.py --package
python tools/install_hwmp24.py
python tools/install_hwmp24.py --install
```

The middle command prints a plan. The last installs only the owned `HomeworldRM/DataWorkshopMODs/HWMPPatch24` folder, after full release/hash validation, and preserves its previous contents under ignored local/installed-backups. Original game archives and other mods are guarded. Unknown files or links in the owned folder stop installation.

## Direct launch

Run `HWMP Patch 2.4.cmd` from that folder for English. Supported overrides: `-Language French`, German, Italian, Spanish or Russian. `-PrintOnly` prints the command without starting the game. The normal game menu opens; choose skirmish/multiplayer. This complete package does not need a second Players Patch.

## Native launcher: one local slot

The installed launcher enumerates Steam subscriptions plus one fixed local `Gearbox/BananaMothership` slot. An arbitrary config folder does not register another entry; fabricated numeric Workshop IDs can be deleted as unsubscribed. An actual Workshop subscription will provide a separate normal entry after publication.

Until then use the reversible selector:

```powershell
python tools/launcher_slot.py hwmp
python tools/launcher_slot.py hwmp --apply
python tools/launcher_slot.py previous --apply
```

The first prints a plan; the second selects HWMP; the third restores the exact previous Vast Reaches slot. The selector never launches the game. In the launcher select **Mods → Remastered → HWMP Patch2.4 → Launch**. Steam's selected game language controls the language archive; optional `-locale Russian` in the launcher's arguments explicitly selects Russian.

Before switching it copies the whole slot to `local/launcher-slot/backups/<UTC>`, verifies every file, then replaces only the selected mod config, its language archives and its own main archive/preview. The original BananaDLC.big remains. The inactive Vast Reaches package is preserved; only one local title is shown at a time. Consumer source/dependency pins are untouched.

Restoration validates ownership and the current inventory. It restores overwritten files and removes only exact, known additions from this activation; it never recursively deletes the slot. Another mod/user change causes a refusal, not an overwrite. Copy failure triggers rollback from the just-verified backup. State and recovery paths stay in ignored local/launcher-slot/state.json.

If interrupted by power loss, keep the backups and inspect state before another switch. Restore the saved previous folder after verifying the exact absolute destination. Never remove the original Banana archive or unrelated Workshop folders.

File/launcher registration checks do not prove normal UI gameplay. RU/EN/other-language standard and2x starts, network acceptance and physical squadron repair remain in CLOSURE_CHECKLIST.md.
