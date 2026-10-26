"""Private constant-damage scout weapon; native family upgrades and paid research."""

import re


def prepare(put, clone_ship, native):
    for race in ("kus", "tai"):
        weapon = native[f"weapon/{race}_scout/{race}_scout.wepn"].read_text(encoding="ascii")
        weapon, n = re.subn(
            r'(AddWeaponResult\(NewWeaponType,"Hit","DamageHealth","Target",)[^,]+,[^,]+,',
            r"\g<1>100,100,",
            weapon,
        )
        assert n == 1
        # Remove randomness and spatial falloff only from this private measuring weapon.
        weapon = re.sub(
            r"setAccuracy\(NewWeaponType,.*?\);",
            "setAccuracy(NewWeaponType,1);",
            weapon,
            flags=re.S,
        )
        weapon = re.sub(
            r"set(?:DamageFalloff|AccuracyFalloff|SpeedvsAccuracyAgainst|MissProperties)\([^;]*\);",
            "",
            weapon,
        )
        weapon = re.sub(
            r"setPenetration\(NewWeaponType,.*?\);",
            "setPenetration(NewWeaponType,5,1);",
            weapon,
            flags=re.S,
        )
        private_weapon = "hwa_damage_" + race
        put(f"weapon/{private_weapon}/{private_weapon}.wepn", weapon)

        def transform(s, race=race, weapon=private_weapon):
            lines = s.splitlines()
            lines = [
                line
                for line in lines
                if not (line.startswith("StartShipWeaponConfig(") and '"Weapon_Gun1"' in line)
            ]
            s = "\n".join(lines).replace('"' + race.title() + '_Scout"', '"' + weapon + '"')
            s = re.sub(
                r'setTacticsMults\(NewShipType,\s*"DAMAGEAPPLIED"[^\r\n;]*;?',
                'setTacticsMults(NewShipType,"DAMAGEAPPLIED",1,1,1);',
                s,
            )
            return s

        clone_ship(race + "_scout", "hwa_damage_" + race, transform)

    def target(s):
        s = re.sub(r"^StartShipWeaponConfig\([^\n]+\);?\s*$", "", s, flags=re.M)
        s = re.sub(r'^StartShipHardPointConfig\([^\n]*,"Weapon",[^\n]+\);?\s*$', "", s, flags=re.M)
        s = re.sub(r"^NewShipType.maxhealth=.*$", "NewShipType.maxhealth=100000", s, flags=re.M)
        s = re.sub(
            r"^NewShipType.(?:regentime|minRegenTime)=.*$",
            lambda m: m[0].split("=")[0] + "=0",
            s,
            flags=re.M,
        )
        s = re.sub(
            r"^NewShipType.(?:sideArmourDamage|rearArmourDamage)\s*=.*$",
            lambda m: m[0].split("=")[0] + "=1",
            s,
            flags=re.M,
        )
        return s

    clone_ship("hgn_torpedofrigate", "hwa_damage_target", target)


def cases(add, volumes):
    result = []
    for race, owner, control, enemy in [("kus", 4, 2, 1), ("tai", 5, 3, 0)]:
        lab = add(
            "damage_" + race + "_lab",
            race + "_researchship",
            [-110000 if race == "kus" else 110000, 0, 100000],
            owner,
        )
        for kind, source_owner in [("old", owner), ("new", owner), ("control", control)]:
            for rep in range(3):
                k = len(result)
                x = -100000 + k % 6 * 38000
                z = -60000 + k // 6 * 65000
                ident = "damage_" + race + "_" + kind + str(rep + 1)
                source = ident + "_source"
                if kind != "new":
                    add(source, "hwa_damage_" + race, [x, 0, z], source_owner)
                volume = ident + "_spawn"
                volumes.append([volume, [x, 0, z], 10])
                target = add(ident + "_target", "hwa_damage_target", [x, 0, z + 600], enemy)
                result.append(
                    dict(
                        id=ident,
                        kind="hw1_damage",
                        race=race,
                        owner=owner,
                        source_player=source_owner,
                        enemy=enemy,
                        variant=kind,
                        rep=rep,
                        driver=1 if kind == "old" and rep == 0 else 0,
                        lab=lab,
                        source=source,
                        source_type="hwa_damage_" + race,
                        target=target,
                        volume=volume,
                        x=x,
                        z=z,
                    )
                )
    return result
