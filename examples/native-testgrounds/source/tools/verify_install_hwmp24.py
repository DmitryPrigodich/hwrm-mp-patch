"""Exercise installer ownership, backup and refusal paths in a disposable game tree."""

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import install_hwmp24 as installer
from hwrm_common import PROJECT, sha


def verify():
    work = PROJECT / "local/installer-checks"
    work.mkdir(parents=True, exist_ok=True)
    checks = []
    with tempfile.TemporaryDirectory(dir=work) as folder:
        root = Path(folder).resolve()
        assert root.is_relative_to(work.resolve())
        game = root / "game"
        mods = game / "HomeworldRM/DataWorkshopMODs"
        mods.mkdir(parents=True)
        foreign = mods / "OtherMod/config.txt"
        foreign.parent.mkdir()
        foreign.write_text("preserve\n")
        target = mods / "HWMPPatch24"
        target.mkdir()
        (target / "foreign.txt").write_text("unowned\n")
        try:
            installer.install(game, True)
        except ValueError as error:
            assert "not an owned" in str(error)
        else:
            raise AssertionError("Unowned target was accepted.")
        assert (target / "foreign.txt").read_text() == "unowned\n"
        (target / "foreign.txt").unlink()
        target.rmdir()
        checks.append("unowned folder rejected before mutation")
        with (
            patch.object(installer, "PROJECT", root / "project"),
            patch.object(installer, "active_processes", return_value=[{"Id": 1}]),
        ):
            try:
                installer.install(game, True)
            except RuntimeError as error:
                assert "Close the game/launcher" in str(error)
            else:
                raise AssertionError("Running process was ignored.")
        assert not target.exists()
        checks.append("running process blocks installation without stopping it")
        with (
            patch.object(installer, "PROJECT", root / "project"),
            patch.object(installer, "active_processes", return_value=[]),
        ):
            first = installer.install(game, True)
            assert first["installed"] and not first["launched"]
            installed = {n: sha(target / n) for n in first["files"]}
            second = installer.install(game, True)
            backup = Path(second["backup"])
            assert {n: sha(backup / n) for n in installed} == installed
            assert foreign.read_text() == "preserve\n"
            checks.extend(
                [
                    "new installation exact hashes",
                    "previous package copied outside game with exact hashes",
                    "other mod preserved",
                ]
            )
            (target / "foreign.txt").write_text("unowned\n")
            try:
                installer.install(game, True)
            except ValueError as error:
                assert "unowned files" in str(error)
            else:
                raise AssertionError("Unowned contents were overwritten.")
            assert (target / "foreign.txt").read_text() == "unowned\n"
            checks.append("owned folder with foreign contents rejected")
    result = {
        "status": "passed",
        "checks": checks,
        "game_launched": False,
        "native_engine_tested": False,
    }
    (work / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))
