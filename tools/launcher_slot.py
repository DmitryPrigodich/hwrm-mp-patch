"""Reversible selection of HWMP in the launcher's single local Banana slot.

The inactive mod is preserved as a full, hash-verified backup outside the game.
Default is a read-only plan. Never launches or closes the game/launcher.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from hwrm_common import GAME, PROJECT, index, save, sha
from hwmp24 import RELEASE
from install_hwmp24 import active_processes, other_mod_files, release_files
from language_data import LANGUAGES

IDENTITY = "HWMP-launcher-slot-v1"
STATE = PROJECT / "local/launcher-slot/state.json"
WORK = PROJECT / "local/launcher-slot"
SLOT_PARTS = ("HomeworldRM", "DataWorkshopMODs", "Gearbox", "BananaMothership")


def inventory(root):
    return {name: sha(path) for name, path in index(root).items()}


def checked_slot(game):
    game = Path(game).resolve(strict=True)
    slot = game.joinpath(*SLOT_PARTS)
    if (
        slot.is_symlink()
        or slot.is_junction()
        or slot.resolve().relative_to(game).parts != SLOT_PARTS
    ):
        raise ValueError("Unsafe launcher slot: " + str(slot))
    if not slot.is_dir() or any(
        path.is_symlink() or path.is_junction() for path in slot.rglob("*")
    ):
        raise ValueError("Slot is missing or contains links.")
    if active_processes(game):
        raise RuntimeError("Close Homeworld/its launcher before switching; no process was stopped.")
    return game, slot


def backup_slot(slot, label, work=WORK):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = work / "backups" / (stamp + "-" + label)
    if destination.exists() or destination.resolve().is_relative_to(slot.resolve()):
        raise ValueError("Unsafe or occupied backup path.")
    shutil.copytree(slot, destination)
    hashes = inventory(slot)
    if inventory(destination) != hashes:
        raise RuntimeError("Backup mismatch; slot was not modified.")
    return destination, hashes


def copy_verified(source, target):
    temporary = target.with_name(".hwmp-switch-" + target.name)
    if temporary.exists():
        raise ValueError("Unexpected staging file: " + str(temporary))
    shutil.copy2(source, temporary)
    if sha(temporary) != sha(source):
        raise RuntimeError("Copy verification failed: " + target.name)
    temporary.replace(target)


def state_for(slot, state_path=STATE):
    if not state_path.exists():
        return None
    value = json.loads(state_path.read_text(encoding="utf8"))
    if value.get("identity") != IDENTITY or Path(value["slot"]).resolve() != slot.resolve():
        raise ValueError("State belongs to a different launcher slot.")
    return value


def switch(mode, apply=False, game=GAME, state_path=STATE, work=WORK, preview=None):
    if mode not in ("hwmp", "previous"):
        raise ValueError("Unknown slot selection.")
    game, slot = checked_slot(game)
    state = state_for(slot, state_path)
    selected = state is not None and state.get("active") == "hwmp"
    if mode == "previous" and not selected:
        return {"changed": False, "active": "previous", "reason": "HWMP is not selected"}

    payload = {"HWMPPatch24.big": RELEASE / "HWMPPatch24.big"}
    if mode == "hwmp":
        release_files()  # Refuse stale or unverified source archives.
        payload.update({language + ".big": RELEASE / (language + ".big") for language in LANGUAGES})
        payload["config.txt"] = RELEASE / "config.txt"
        if preview is not None:
            preview = Path(preview).resolve(strict=True)
            if preview.suffix.lower() not in (".jpg", ".png"):
                raise ValueError("Preview must be JPG or PNG.")
            payload["preview.jpg" if preview.suffix.lower() == ".jpg" else "preview.png"] = preview
    if selected:
        if inventory(slot) != state["active_inventory"]:
            raise ValueError(
                "Selected slot changed outside this switcher; preserve/review changes first."
            )
    else:
        config = (slot / "config.txt").read_text(encoding="utf8")
        if (
            "BigFilename: VastReachesMiniCampaign.big" not in config
            or not (slot / "VastReachesMiniCampaign.big").is_file()
        ):
            raise ValueError(
                "First selection expects the reviewed Vast Reaches slot; refusing an unknown mod."
            )

    plan = {
        "identity": IDENTITY,
        "mode": mode,
        "slot": str(slot),
        "changed": False,
        "ordinary_slot_unchanged": True,
        "game_launched": False,
    }
    if not apply:
        return plan

    mods = game / "HomeworldRM/DataWorkshopMODs"
    other_before = other_mod_files(mods, slot)
    banana = {
        str(path): sha(path)
        for path in (slot / "BananaDLC.big", game / "HomeworldRM/Data/BananaDLC.big")
        if path.is_file()
    }
    rollback, before = backup_slot(slot, "before-" + mode, work)
    previous_backup = Path(state["previous_backup"]) if selected else rollback
    previous_inventory = state["previous_inventory"] if selected else before
    if inventory(previous_backup) != previous_inventory:
        raise ValueError("The preserved previous mod no longer matches its backup.")
    try:
        if mode == "hwmp":
            # Keep the old config until all new archives exist; nobody is running.
            for name, source in payload.items():
                if name != "config.txt":
                    copy_verified(source, slot / name)
            copy_verified(payload["config.txt"], slot / "config.txt")
            after = inventory(slot)
            for name, source in payload.items():
                if after[name.lower()] != sha(source):
                    raise RuntimeError("Selected payload differs from release: " + name)
            next_state = {
                "identity": IDENTITY,
                "slot": str(slot),
                "active": "hwmp",
                "previous_backup": str(previous_backup),
                "previous_inventory": previous_inventory,
                "active_inventory": after,
            }
        else:
            for name, source in index(previous_backup).items():
                copy_verified(source, slot / source.relative_to(previous_backup))
            # Remove only additions owned by this activation; never recurse.
            for name, path in index(slot).items():
                if name not in previous_inventory:
                    if (
                        name in before
                        and path.resolve().parent == slot.resolve()
                        and sha(path) == before[name]
                    ):
                        path.unlink()
                    else:
                        raise ValueError("Refusing to remove an unowned added path: " + name)
            if inventory(slot) != previous_inventory:
                raise RuntimeError("Previous slot restoration differs from its backup.")
            next_state = {**state, "active": "previous", "restored_inventory": previous_inventory}
        if (
            other_mod_files(mods, slot) != other_before
            or {name: sha(Path(name)) for name in banana} != banana
        ):
            raise RuntimeError("Another mod or original Banana archive changed.")
    except Exception:
        for name, source in index(rollback).items():
            copy_verified(source, slot / source.relative_to(rollback))
        for name, path in index(slot).items():
            if (
                name not in before
                and name in {key.lower() for key in payload}
                and path.resolve().parent == slot.resolve()
            ):
                path.unlink()
        if inventory(slot) != before:
            raise RuntimeError("Automatic rollback needs manual recovery from " + str(rollback))
        raise
    save(state_path, next_state)
    plan.update(
        changed=True,
        active=next_state["active"],
        rollback=str(rollback),
        other_mods_unchanged=True,
        original_banana_unchanged=True,
    )
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection", choices=("hwmp", "previous"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--game-root", type=Path, default=GAME)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            switch(args.selection, args.apply, args.game_root, preview=args.preview), indent=2
        )
    )
