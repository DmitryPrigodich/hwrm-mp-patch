"""Three repeated native subsystem knockouts, with an alternate drop-off control."""


def cases(add, volumes, asteroids):
    result = []
    for rep, (receiver_type, distance, alternative) in enumerate(
        [("mothership", 5000, 0), ("carrier", 13000, 0), ("mothership", 5000, 1)]
    ):
        z = -80000 + rep * 80000
        for offset, race in enumerate(("hgn", "vgr")):
            owner = rep * 2 + offset
            x = -100000 if offset == 0 else 100000
            name = "raids_" + race + "_" + str(rep)
            receiver = (
                "HWA_MotherH" if owner == 0 else "HWA_MotherV" if owner == 1 else name + "_receiver"
            )
            add(receiver, race + "_" + receiver_type, [x, 0, z], owner)
            backup = ""
            if alternative:
                backup = add(
                    name + "_alternate", race + "_resourcecontroller", [x, 0, z + 3500], owner
                )
            members = [
                add(
                    name + "_" + str(j),
                    race + "_resourcecollector",
                    [x - 1000 + j * 300, 0, z + 2000],
                    owner,
                )
                for j in range(6)
            ]
            for j in range(48):
                asteroids.append(
                    [
                        "Asteroid_3",
                        [x + (j % 8 - 4) * 500, (j % 3 - 1) * 350, z + distance + j // 8 * 600],
                    ]
                )
            result.append(
                dict(
                    id=name,
                    kind="economy_raids",
                    race=race,
                    player=owner,
                    receiver=receiver,
                    receiver_type=receiver_type,
                    distance=distance,
                    backup=backup,
                    members=members,
                    count=6,
                    damage_times=[120, 300, 480],
                    finish=720,
                    x=x,
                    z=z,
                )
            )
    return result
