"""Source/native-Lua-parser contracts for Cataclysm. No native gameplay claim."""

import json
import re
import subprocess

from lupa.lua51 import LuaRuntime
from cataclysm import FAMILY, MODE, RETAINED, SCALE, model, patch_ship
from hwrm_common import CACHE, DONOR, PROJECT, index, save, sha
from hwrm_inspect import record_config, plain
from production_data import stock_files
from project_version import VERSION


def verify():
    design = model()
    from cataclysm_descriptions import description_ids
    from verify_cataclysm_descriptions import verify as verify_descriptions

    ids = description_ids(design)
    out = PROJECT / "hwmp-patch-2.4/overrides"
    native = stock_files()
    native.update(index(DONOR))
    files = index(out)
    ship_checks = []
    zero_supplies = {}
    for ident, row in sorted(design["ships"].items()):
        relative = f"ship/{ident}/{ident}.ship"
        old = native[relative].read_text(encoding="utf-8-sig")
        new = files[relative].read_text(encoding="ascii")
        assert new == patch_ship(old, row["su_per_group"], ids[ident]), relative
        baseline, calls = record_config(old)
        normal, normal_calls = record_config(new)
        cat, cat_calls = record_config(new, rule_props={"hwmp_cataclysm": 1})
        assert baseline == normal, ("Ordinary ship fields changed", ident)
        expected_cat = dict(baseline, sobDescription="$" + str(ids[ident]))
        assert cat == expected_cat, ("Unexpected Cataclysm ship fields changed", ident)
        assert calls == normal_calls, ("Ordinary mode changed", ident)
        expected = []
        for name, args in calls:
            if (
                name != "setSupplyValue"
                or args[0].lower().startswith("layout")
                or args[0].lower() in RETAINED
            ):
                expected.append((name, args))
        expected.append(("setSupplyValue", [FAMILY, row["su_per_group"] / SCALE]))
        assert cat_calls == expected, ("Wrong Cataclysm supply", ident)
        assert row["su_per_hull"] * row["build_batch"] == row["su_per_group"]
        if ident.endswith("_carrier"):
            assert row["su_per_group"] == 40 and ("setSupplyValue", ["Carrier", 1]) in cat_calls
        if ident.endswith("_shipyard"):
            assert row["su_per_group"] == 50 and ("setSupplyValue", ["Shipyard", 1]) in cat_calls
        if row["su_per_group"] == 0:
            kept = {
                args[0]: args[1]
                for name, args in cat_calls
                if name == "setSupplyValue" and args[0].lower() in RETAINED
            }
            assert kept, ("Zero-SU ship is unbounded", ident)
            zero_supplies[ident] = (row["race"], kept)
        ship_checks.append(ident)

    vm = LuaRuntime(register_eval=False, register_builtins=False)
    vm.globals().dofilepath = lambda *args: None
    rules = files[f"scripts/rules/{MODE}.lua"].read_text(encoding="ascii")
    vm.execute(rules)
    assert vm.globals().GameRulesName == f"HWMP {VERSION} Cataclysm"
    assert "HWMP_Cataclysm" in vm.globals().Race_Paths
    assert "2x_race_dm" not in vm.globals().Race_Pass_Tags
    options = plain(vm.globals().GameSetupOptions)
    profiles = next(v for v in options.values() if v["name"] == "unitcaps")["choices"]
    assert {v.lower() for k, v in profiles.items() if k % 2 == 0} == set(design["budgets"])
    props = LuaRuntime(register_eval=False, register_builtins=False)
    props.execute(files[f"scripts/rules/{MODE}/props/default.lua"].read_text())
    assert props.globals().Number_Properties["hwmp_cataclysm"] == 1
    caps = {}
    for profile, budget in design["budgets"].items():
        relative = f"scripts/rules/{MODE}/unitcaps/{profile}.lua"
        text = files[relative].read_text()
        found = re.search(r'supplyLimit\("' + FAMILY + r'", ([0-9.]+)\)', text)
        assert found and float(found[1]) * SCALE == budget
        assert budget % SCALE == 0 and budget / SCALE < 250
        for race in design["races"]:
            ordinary = f"scripts/races/{race}/deathmatch/unitcaps/{profile}.lua"
            alternate = f"scripts/races/{race}/hwmp_cataclysm/unitcaps/{profile}.lua"
            assert files[alternate].read_text() == native[ordinary].read_text()
            both = text + files[alternate].read_text()
            values = dict(re.findall(r'supplyLimit\("([^\"]+)"\s*,\s*([0-9.]+)\)', both))
            caps[race + "/" + profile] = int(float(values["Carrier"]))
    assert caps["vaygr/normal"] == 4 and caps["vaygr/huge"] == 5
    zero_caps = {}
    for ident, (race, supplies) in zero_supplies.items():
        zero_caps[ident] = {}
        for profile in design["budgets"]:
            old = (
                native[f"scripts/rules/deathmatch/unitcaps/{profile}.lua"].read_text()
                + native[f"scripts/races/{race}/deathmatch/unitcaps/{profile}.lua"].read_text()
            )
            new = (
                files[f"scripts/rules/{MODE}/unitcaps/{profile}.lua"].read_text()
                + files[f"scripts/races/{race}/hwmp_cataclysm/unitcaps/{profile}.lua"].read_text()
            )

            def limits(code):
                return {
                    k: float(v)
                    for k, v in re.findall(r'supplyLimit\("([^\"]+)"\s*,\s*([0-9.]+)\)', code)
                }

            before, after = limits(old), limits(new)
            zero_caps[ident][profile] = {family: after[family] for family in supplies}
            assert all(after[family] == before[family] and after[family] > 0 for family in supplies)

    # HUD recomputes current ownership and does not mutate the simulated world.
    hud = files["scripts/hwmp24/cataclysm_hud.lua"].read_text(encoding="ascii")
    hud = re.sub(
        r"for ship, cost in HWMP_CataclysmCosts do",
        "for ship, cost in pairs(HWMP_CataclysmCosts) do",
        hud,
    )
    h = LuaRuntime(register_eval=False, register_builtins=False)
    counts = {}
    labels = []
    h.globals().dofilepath = lambda *a: None
    h.globals().Universe_CurrentPlayer = lambda: 0
    h.globals().Universe_PlayerCount = lambda: 2
    h.globals().UI_IsScreenActive = lambda screen: 1
    h.globals().GetGameSettingAsString = lambda key: "Normal"
    h.globals().strlower = str.lower
    h.globals().Player_GetNumberOfSquadronsOfTypeAwakeOrSleeping = lambda player, ident: counts.get(
        ident, 0
    )
    h.globals().UI_SetElementVisible = lambda *a: None
    h.globals().UI_SetTextLabelText = lambda *a: labels.append(a[-1])
    h.globals().HWMP_CataclysmOwned = "Owned fleet SU"
    h.execute(hud)
    counts.update(hgn_interceptor=2, vgr_interceptor=1, hgn_carrier=1)
    assert h.globals().HWMP_CataclysmUpdateHUD() == 84
    counts.clear()  # Capture/destruction/save rewind is read from current world counts.
    counts.update(vgr_battlecruiser=1)
    assert h.globals().HWMP_CataclysmUpdateHUD() == 150
    assert labels[-1].endswith("150/" + str(design["budgets"]["normal"]))
    h.globals().UI_IsScreenActive = lambda screen: 0
    before = len(labels)
    h.globals().HWMP_CataclysmUpdateHUD()
    assert len(labels) == before + 1
    assert labels[-1].endswith("150/" + str(design["budgets"]["normal"]))
    # Closed-popup prepopulation: an opening window receives existing text/size.
    for profile, budget in design["budgets"].items():
        h.globals().GetGameSettingAsString = lambda key, value=profile: value
        assert h.globals().HWMP_CataclysmUpdateHUD() == 150
        assert labels[-1].endswith("150/" + str(budget))
    h.globals().GetGameSettingAsString = lambda key: "unknown-profile"
    assert h.globals().HWMP_CataclysmUpdateHUD() == 150
    assert labels[-1].endswith("150/?")  # An unresolved setting is visible, not a blank row.
    assert all(
        label.isascii() for label in labels
    ), "Runtime text setters must only carry ASCII counters"
    assert "UnitCapInfoPopup" not in hud
    from cataclysm import HUD_ENABLED

    assert HUD_ENABLED is True
    assert (
        files["ui/newui/unitcapinfopopup.lua"].read_text()
        == (CACHE / "players-patch-audit/rm-base/ui/newui/unitcapinfopopup.lua").read_text()
    )
    assert (
        files["ui/newui/newtaskbar.lua"].read_text()
        == (DONOR / "ui/newui/newtaskbar.lua").read_text()
    )
    resource = files["ui/newui/resource.lua"].read_text()
    assert 'name = "HWMP_SURow"' in resource and 'text="$9684401"' in resource
    assert resource.count('anchorName = "Taskbar_ResourceBottomCenter3"') == 1
    assert resource.count('pivotY = "HWMP_ResourceBottomLeft"') == 1
    assert "relativePos={0,1}" in resource and "uvRect = {0,1,1,0}" in resource
    assert '"ResourceMenu", "HWMP_SUOwned"' in hud
    icon = files["ui/newui/ingameicons/hwmp_support_units.tga"].read_bytes()
    assert icon[2] == 2 and len(icon) == 18 + 128 * 128 * 4
    assert icon[16:18] == bytes([32, 8])
    assert any(icon[i] == 0 for i in range(21, len(icon), 4))
    assert any(icon[i] == 255 for i in range(21, len(icon), 4))
    native_callbacks = files["scripts/rules/deathmatch/deathmatch.lua"].read_text()
    assert "Rules_GetNumber" not in native_callbacks
    assert 'if GameRulesName == "HWMP 2.4.5 Cataclysm" then' in native_callbacks

    menu = LuaRuntime(register_eval=False, register_builtins=False)
    menu.execute(files["ui/newui/background/logo.lua"].read_text())
    children = plain(menu.globals().BACKGROUND_LOGO)
    names = [children[i]["name"] for i in (2, 3, 4, 5)]
    assert names == [
        "HWMP_HiigaranEmblem",
        "HWMP_VaygrEmblem",
        "HWMP_TaiidanEmblem",
        "HWMP_KushanEmblem",
    ]
    assert [children[i]["Layout"]["pos_XY"]["x"] for i in (2, 3, 4, 5)] == [0.17, 0.39, 0.61, 0.83]
    assert (
        sha(files["ui/newui/background/hwmp24_kushan.tga"])
        == "d11829f8fe690eeb3c73909bf98f521cedb6669035162706da05c26eef291ad1"
    )

    compiler = CACHE / "hwmp-testgrounds-step/lua4/lua-4.0.1/luac4-x86.exe"
    parsed = []
    for name, path in files.items():
        if path.suffix.lower() not in (".lua", ".ship", ".wepn", ".subs", ".miss", ".wf"):
            continue
        result = subprocess.run([str(compiler), "-p", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        parsed.append(name)
    report = {
        "status": "passed",
        "descriptions": verify_descriptions(out, design),
        "version": VERSION,
        "ships_checked_both_modes": len(ship_checks),
        "ordinary_ship_fields_and_calls_unchanged": True,
        "native_scale": SCALE,
        "budgets": design["budgets"],
        "carrier_bonus": False,
        "zero_su_native_caps": zero_caps,
        "carrier_caps": caps,
        "hud_mock": "Own-group arithmetic; UI and callback contexts matched to the native probe",
        "hud_enabled": True,
        "lua4_parsed": len(parsed),
        "four_native_menu_emblems": names,
        "native_engine_tested": False,
        "installed": False,
    }
    save(PROJECT / "local/cataclysm/verification.json", report)
    return report


if __name__ == "__main__":
    print(json.dumps(verify()))
