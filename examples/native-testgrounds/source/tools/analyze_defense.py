"""Evidence-based defense checks. Raw native measurements remain unchanged."""

from collections import Counter, defaultdict
from statistics import mean


def summarize(plans, results, events):
    checks = []
    pairs = defaultdict(dict)
    for r in results:
        c = plans[r["case"]]
        ev = [e for e in events if e["case"] == r["case"]]
        attacks = [e for e in ev if e["event"] == "defense_attack_selection"]
        scans = [e for e in ev if e["event"] == "defense_scan" and int(e["global_missiles"]) > 0]
        attack_order = int(next(e["command_attack"] for e in ev if e["event"] == "baseline"))
        orders = [e for e in ev if "order" in e]
        ever_attack = any(int(e["order"]) == attack_order for e in orders)
        row = {
            "case": r["case"],
            "action": c["action"],
            "variant": c["variant"],
            "native_status": r["status"],
            "commands_phase1": sum(e["phase"] == "1" for e in attacks),
            "commands_phase2": sum(e["phase"] == "2" for e in attacks),
            "commands_full_phase2": sum(
                e["phase"] == "2" and int(e["selected_missiles"]) == c["volley"] for e in attacks
            ),
            "positive_scans": len(scans),
            "ever_attack_order": ever_attack,
            "final_guarding": int(r["guarding"]),
            "same_cache_scans_phase2": sum(
                e["phase"] == "2" and e["global_missiles"] == e["previous_count"] for e in scans
            ),
            "old_snapshot_before_second": next(
                (
                    int(e["old_alive"])
                    for e in ev
                    if e["event"] == "fire_requested" and e.get("phase") == "2"
                ),
                None,
            ),
            "damage": float(r["target_damage"]),
        }
        if c["action"] == "intercept":
            row["check"] = "measurement"
            row["status"] = r["status"]
            pairs[(c["ammo"], c["rep"])][c["variant"]] = row
        elif c["action"] == "attack_order":
            row["check"] = "explicit_player_order_experiment"
            row["status"] = r["status"]
        else:
            row["check"] = "native_selection_invariant"
            row["status"] = "blocked"
            if r["status"] == "measured":
                if c["action"] in ("ally", "own", "far"):
                    callbacks = [e for e in ev if e["event"] == "defense_callback"]
                    row["status"] = (
                        "passed"
                        if callbacks and scans and not attacks and row["final_guarding"] == 1
                        else "failed"
                    )
                elif c["action"] == "enemy":
                    row["status"] = (
                        "passed" if attacks and scans and row["final_guarding"] == 1 else "failed"
                    )
                elif c["action"] == "same_count":
                    prepared = any(
                        e["event"] == "guard_reissued" and int(e["current_count"]) == c["volley"]
                        for e in ev
                    )
                    paused = any(
                        e["event"] == "observer_paused" and int(e["current_count"]) == c["volley"]
                        for e in ev
                    )
                    second_scans = [e for e in scans if e["phase"] == "2"]
                    equal_on_resume = bool(
                        second_scans
                        and int(second_scans[0]["previous_count"])
                        == int(second_scans[0]["global_missiles"])
                        == c["volley"]
                    )
                    valid = (
                        prepared
                        and paused
                        and equal_on_resume
                        and row["old_snapshot_before_second"] == 0
                        and row["same_cache_scans_phase2"] > 0
                        and int(r["first_peak"]) == int(r["second_peak"]) == c["volley"]
                    )
                    if valid:
                        observed = row["commands_full_phase2"] > 0
                        row["status"] = (
                            "passed" if observed == (c["variant"] == "applied") else "failed"
                        )
                        if c["variant"] == "control":
                            row["check"] = "upstream_negative_control_reproduced"
        row["guard_return"] = (
            "passed"
            if ever_attack and row["final_guarding"] == 1
            else "not_exercised" if not ever_attack else "failed"
        )
        if c["action"] == "attack_order":
            row["guard_return"] = (
                "manual_Stop_then_Attack_replaced_guard_not_automatic_interception"
            )
        checks.append(row)
    summary = []
    for (ammo, rep), pair in sorted(pairs.items()):
        if set(pair) == {"none", "stock"}:
            a, b = pair["none"], pair["stock"]
            summary.append(
                {
                    "ammo": ammo,
                    "rep": rep,
                    "baseline_damage": a["damage"],
                    "defended_damage": b["damage"],
                    "damage_reduction": a["damage"] - b["damage"],
                    "native_statuses": [a["native_status"], b["native_status"]],
                    "ever_attack_order": b["ever_attack_order"],
                    "final_guarding": b["final_guarding"],
                }
            )
    return {
        "checks": checks,
        "invariant_counts": dict(
            Counter(
                r["status"]
                for r in checks
                if r["check"] not in ("measurement", "explicit_player_order_experiment")
            )
        ),
        "interception_pairs": summary,
        "interception_means": [
            {
                "ammo": ammo,
                "n": len(rows),
                "baseline_damage": mean(r["baseline_damage"] for r in rows),
                "defended_damage": mean(r["defended_damage"] for r in rows),
                "mean_reduction": mean(r["damage_reduction"] for r in rows),
            }
            for ammo in sorted({r["ammo"] for r in summary})
            if (
                rows := [
                    r
                    for r in summary
                    if r["ammo"] == ammo and r["native_statuses"] == ["measured", "measured"]
                ]
            )
        ],
        "raw_measurements_not_relabelled": True,
        "equal_count_stimulus": "cohort1 gone, native Stop, cohort2 complete, Guard resumed without cache reset",
    }
