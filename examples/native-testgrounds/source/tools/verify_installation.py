"""Temporary-filesystem checks for owned installation, rollback and slot restoration."""

import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import install_hwmp24 as installer
import launcher_slot
from hwrm_common import index, sha
from hwmp24 import IDENTITY
from language_data import LANGUAGES


def expect_error(function, error):
    try:
        function()
    except error:
        return
    raise AssertionError("Expected refusal: " + error.__name__)


def verify():
    with tempfile.TemporaryDirectory(prefix="hwmp-installation-fixture-") as temporary:
        root = Path(temporary)
        release = root / "release"
        release.mkdir()
        for name in installer.PAYLOAD:
            (release / name).write_text("fixture:" + name, encoding="utf8")
        (release / "version.json").write_text(
            json.dumps({"identity": IDENTITY, "fix_revision": "fixture"})
        )
        sums = {path.name: sha(path) for path in release.iterdir()}
        (release / "SHA256SUMS.txt").write_text(
            "".join(digest + "  " + name + "\n" for name, digest in sorted(sums.items()))
        )
        work = root / "verification"
        work.mkdir()
        (work / "verification-package.json").write_text(
            json.dumps(
                {
                    "status": "passed",
                    "full_extract_hash_comparison": True,
                    "archives": [
                        {"archive": name, "sha256": sums[name]}
                        for name in [
                            "HWMPPatch24.big",
                            *[language + ".big" for language in LANGUAGES],
                        ]
                    ],
                }
            )
        )
        game = root / "game"
        mods = game / "HomeworldRM/DataWorkshopMODs"
        slot = mods / "Gearbox/BananaMothership"
        slot.mkdir(parents=True)
        (slot / "config.txt").write_text(
            "Title: Vast Reaches Campaign Demo\nBigFilename: VastReachesMiniCampaign.big\n"
        )
        for name in ("VastReachesMiniCampaign.big", "English.big", "Russian.big", "BananaDLC.big"):
            (slot / name).write_bytes(("original:" + name).encode())
        (mods / "unrelated.txt").write_text("preserve me")
        original = launcher_slot.inventory(slot)
        with (
            patch.object(installer, "RELEASE", release),
            patch.object(installer, "WORK", work),
            patch.object(installer, "PROJECT", root),
            patch.object(installer, "active_processes", return_value=[]),
        ):
            plan = installer.install(game)
            assert not plan["installed"] and not (mods / "HWMPPatch24").exists()
            installer.install(game, True)
            installer.install(game, True)
            assert (mods / "unrelated.txt").read_text() == "preserve me"
            assert launcher_slot.inventory(slot) == original
            (mods / "HWMPPatch24/unowned.txt").write_text("do not replace")
            expect_error(lambda: installer.install(game, True), ValueError)
            (mods / "HWMPPatch24/unowned.txt").unlink()
            with (
                patch.object(launcher_slot, "RELEASE", release),
                patch.object(launcher_slot, "active_processes", return_value=[]),
            ):
                state = root / "slot/state.json"
                workspace = root / "slot"
                args = dict(game=game, state_path=state, work=workspace)
                launcher_slot.switch("hwmp", True, **args)
                assert (slot / "BananaDLC.big").read_bytes() == b"original:BananaDLC.big"
                (slot / "foreign.txt").write_text("new user change")
                expect_error(lambda: launcher_slot.switch("previous", True, **args), ValueError)
                (slot / "foreign.txt").unlink()
                launcher_slot.switch("previous", True, **args)
                assert launcher_slot.inventory(slot) == original
                assert (mods / "unrelated.txt").read_text() == "preserve me"
                # A failed copy after mutation must restore the exact former slot.
                copy = launcher_slot.copy_verified
                failed = [False]

                def fail_once(source, target):
                    if target.name == "French.big" and not failed[0]:
                        failed[0] = True
                        raise OSError("injected copy failure")
                    return copy(source, target)

                with patch.object(launcher_slot, "copy_verified", side_effect=fail_once):
                    expect_error(lambda: launcher_slot.switch("hwmp", True, **args), OSError)
                assert launcher_slot.inventory(slot) == original
            (release / "English.big").write_text("corrupted")
            expect_error(installer.release_files, ValueError)
    return {
        "status": "passed",
        "fixture_only": True,
        "checks": [
            "read-only plan",
            "shared payload",
            "repeat/backup",
            "unowned refusal",
            "checksum refusal",
            "slot roundtrip",
            "user change refusal",
            "copy-failure rollback",
            "original/unrelated files preserved",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(verify()))
