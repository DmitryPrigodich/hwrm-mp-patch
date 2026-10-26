"""Real support-frigate docking and hyperspace, with mixed passenger baselines."""


def cases(add, volumes):
    result = []
    for race, owner in (("kus", 4), ("tai", 5)):
        for action in ("normal", "stop", "destroy"):
            k = len(result)
            x = -90000 + (k % 3) * 80000
            z = -60000 + (k // 3) * 120000
            name = "transport_" + race + "_" + action
            carrier = add(name + "_carrier", race + "_supportfrigate", [x, 0, z], owner)
            members = [
                add(name + "_p1", race + "_scout", [x + 300, 0, z + 600], owner),
                add(name + "_p2", race + "_lightcorvette", [x - 300, 0, z + 900], owner),
            ]
            volume = name + "_destination"
            volumes.append([volume, [x, 0, z + 45000], 100])
            result.append(
                {
                    "id": name,
                    "kind": "transport",
                    "race": race,
                    "owner": owner,
                    "action": action,
                    "carrier": carrier,
                    "members": members,
                    "member_types": [race + "_scout", race + "_lightcorvette"],
                    "destination": volume,
                    "x": x,
                    "z": z,
                }
            )
    return result
