"""Derived native Dock invariants; raw observations remain unchanged."""

from collections import defaultdict, Counter


def summarize(plans, results, events):
    checks = []
    for result in results:
        case = result["case"]
        c = plans[case]
        rows = [
            e
            for e in events
            if e.get("case") == case and e.get("event") in ("dock_callback", "dock_retry")
        ]
        by_id = defaultdict(list)
        for e in rows:
            by_id[e.get("ship_id", "unknown")].append(e)
        retries = []
        early = []
        invalid = []
        intervals = []
        repeated_ids = 0
        for ident, items in by_id.items():
            since = None
            last_retry = None
            n = 0
            for e in items:
                t = float(e["t"])
                eligible = (
                    int(e.get("order", -1)) == int(e.get("expected_dock_order", 4))
                    and e.get("under_attack") == "1"
                    and float(e.get("actual_speed", 999)) < 1
                    and e.get("can_move") == "1"
                    and e.get("can_dock") == "1"
                    and e.get("docked") == "0"
                )
                if e["event"] == "dock_callback":
                    if eligible:
                        if since is None:
                            since = t
                    else:
                        since = None
                else:
                    retries.append(e)
                    n += 1
                    if not eligible:
                        invalid.append(e)
                    if since is None or t - since < 2.999:
                        early.append(e)
                    if last_retry is not None:
                        intervals.append(t - last_retry)
                    last_retry = t
                    since = t
            if n >= 2:
                repeated_ids += 1
        status = "passed"
        reason = "native eligibility/timing controls"
        if not rows:
            status = "blocked"
            reason = "native callback trace absent"
        elif any(e.get("ship_id", "unknown") == "unknown" for e in rows):
            status = "blocked"
            reason = "per-hull trace unavailable"
        elif c["action"] == "stall" and (
            int(result.get("stalled_under_fire_samples", 0)) == 0
            or not retries
            or repeated_ids == 0
        ):
            status = "blocked"
            reason = "forced retry branch not demonstrated"
        elif invalid or early or intervals and min(intervals) < 4.999:
            status = "failed"
            reason = "invalid/early/too-frequent native retry"
        elif c["action"] == "stall" and result.get("docked") != "1":
            status = "failed"
            reason = "not docked after fixture release"
        checks.append(
            dict(
                case=case,
                action=c["action"],
                status=status,
                reason=reason,
                callback_events=len(rows) - len(retries),
                retry_events=len(retries),
                repeated_hull_ids=repeated_ids,
                min_retry_interval=min(intervals) if intervals else None,
                invalid_retries=len(invalid),
                early_retries=len(early),
                native_status=result["status"],
                docked=result.get("docked"),
            )
        )
    return dict(
        checks=checks,
        invariant_counts=dict(Counter(c["status"] for c in checks)),
        raw_measurements_not_relabelled=True,
        speed_zero_is_fixture=True,
        fire_is_native=True,
        fallback_dock_enum_for_early_logs=4,
        physical_hull_count_not_inferred=True,
    )
