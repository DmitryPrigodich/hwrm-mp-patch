"""Paid native AI Build requests, with only one eligible carrier per phase."""


def cases(add, volumes):
    result = []
    for player, race, upgrade in [(2, "hgn", 1), (1, "vgr", 1), (4, "hgn", 0), (5, "vgr", 0)]:
        k = len(result)
        x = -90000 + k * 60000
        z = 30000
        name = "production_" + race + ("_upgrade" if upgrade else "_control")
        mother = add(name + "_mother", race + "_mothership", [x, 0, z - 12000], player)
        old = add(name + "_old", race + "_carrier", [x, 0, z], player)
        fresh = name + "_new"
        volume = name + "_new_volume"
        volumes.append([volume, [x + 6000, 0, z], 100])
        result.append(
            dict(
                id=name,
                kind="paid_production",
                race=race,
                player=player,
                upgrade=upgrade,
                mother=mother,
                old=old,
                fresh=fresh,
                volume=volume,
                carrier_type=race + "_carrier",
                item=race + "_interceptor",
                item_id=race.upper() + "_INTERCEPTOR",
                item_cost=450,
                item_base_time=35,
                tech="CarrierBUILDSPEEDUpgrade1",
                research_cost=2250 if race == "hgn" else 2500,
                x=x,
                z=z,
            )
        )
    return result
