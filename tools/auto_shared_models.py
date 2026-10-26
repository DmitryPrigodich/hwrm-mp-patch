"""Native load/launch/impact smoke for the three deduplicated missile models."""

import re


def prepare(put, clone_ship, native):
    for tag, weapon in (
        ("small", "Vgr_ConcussionMissileLauncher"),
        ("antifighter", "Vgr_ConcussionMissileLauncher_Medium"),
    ):

        def transform(text, weapon=weapon):
            lines = re.findall(r"^StartShipWeaponConfig\([^\n]+\);?\s*$", text, re.M)
            keep = [line for line in lines if '"' + weapon + '"' in line]
            assert len(keep) == 1, (weapon, keep)
            return (
                re.sub(r"^StartShipWeaponConfig\([^\n]+\);?\s*$", "", text, flags=re.M)
                + "\n"
                + keep[0]
                + "\n"
            )

        clone_ship("vgr_missilecorvette", "hwa_shared_" + tag, transform)


def cases(add):
    result = [{"id": "stock_mothership", "kind": "shared_model", "load_only": 1}]
    for i, (tag, ship, missile) in enumerate(
        (
            ("small", "hwa_shared_small", "Vgr_CorvetteSmallMissile"),
            ("antifighter", "hwa_shared_antifighter", "Vgr_CorvetteAntiFighterMissile"),
            ("medium", "hwa_launcher_hmf", "Vgr_MediumMissile"),
        )
    ):
        x, z = -45000 + i * 40000, 0
        source = add("shared_" + tag + "_source", ship, [x, 0, z], 1)
        target = add(
            "shared_" + tag + "_target",
            "hwa_probe_light" if tag == "antifighter" else "hwa_probe_medium",
            [x, 0, z + 1500],
            0,
        )
        result.append(
            {
                "id": "shared_" + tag,
                "kind": "shared_model",
                "source": source,
                "target": target,
                "source_player": 1,
                "missile": missile,
                "x": x,
                "z": z,
            }
        )
    return result
