"""Native old/new hull HP and route speed after granted research, with controls."""


def cases(add, volumes):
    result = []
    for player, race, upgraded in [(0, "hgn", 1), (1, "vgr", 1), (2, "hgn", 0), (3, "vgr", 0)]:
        x = -90000 + player * 60000
        z = 30000
        name = "effects_" + race + ("_upgraded" if upgraded else "_control")
        mother = add(name + "_mother", race + "_mothership", [x, 0, z - 7000], player)
        kinds = [
            race + "_interceptor",
            race + "_scout",
            race + "_torpedofrigate" if race == "hgn" else race + "_assaultfrigate",
            race + "_ioncannonfrigate" if race == "hgn" else race + "_heavymissilefrigate",
        ]
        members = []
        fresh = []
        starts = []
        routes = []
        for j, kind in enumerate(kinds):
            p = [x + j * 1200 - 1800, 0, z]
            members.append(add(name + "_old" + str(j), kind, p, player, 0 if j < 2 else 1))
            fresh.append(name + "_fresh" + str(j))
            start = name + "_spawn" + str(j)
            volumes.append([start, [p[0] + 500, 0, z], 50])
            starts.append(start)
            route = name + "_route" + str(j)
            volumes.append([route, [p[0], 0, z + 60000], 100])
            routes.append(route)
        result.append(
            dict(
                id=name,
                kind="research_effects",
                race=race,
                player=player,
                upgraded=upgraded,
                mother=mother,
                types=kinds,
                members=members,
                fresh=fresh,
                starts=starts,
                routes=routes,
                speed_tech=(
                    "InterceptorMAXSPEEDUpgrade1" if race == "hgn" else "FighterspeedUpgrade1"
                ),
                hp_tech=(
                    "TorpedoFrigateHealthUpgrade1" if race == "hgn" else "FrigateHealthUpgrade1"
                ),
                x=x,
                z=z,
            )
        )
    return result
