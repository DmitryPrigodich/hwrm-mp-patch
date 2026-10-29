"""Generate HWMP Cataclysm on existing ship IDs. Preparation only, never launch.

The selected Game Type's numeric property gates supply at static definition load.
Ordinary configuration and all Layout supplies remain byte/semantically intact.
Native supply is scaled by 32 (exact binary fractions); HUD displays nominal SU.
"""

import json
from pathlib import Path
import re

from hwrm_common import CACHE, DONOR, PROJECT, index, save, sha
from production_data import stock_files
from project_version import VERSION

FAMILY = "HWMP_SupportUnits"
MODE = "hwmpcataclysm"
SCALE = 32
HUD_ENABLED = True  # Pure GameRulesName gate; supported by the native context probe.
DESIGN = PROJECT / "design/cataclysm.json"
RETAINED = {
    "carrier",
    "shipyard",
    "mothership",
    "probe",
    "probe_hw1",
    "ecmprobe",
    "proximitysensor",
    "proximitysensor_hw1",
    "research",
    "research1",
    "research2",
    "research3",
    "research4",
    "research5",
}


def model():
    return json.loads(DESIGN.read_text(encoding="utf8"))


def ship_paths():
    return {f"ship/{ident}/{ident}.ship" for ident in model()["ships"]}


def patch_ship(text, cost, description_key=None):
    first = "NewShipType = StartShipConfig()"
    if text.count(first) != 1:
        raise ValueError("Unexpected ship constructor")
    text = text.replace(
        first,
        first + '\nlocal HWMP_CataclysmShip = getRulesNum(NewShipType, "hwmp_cataclysm", 0) == 1',
        1,
    )
    pattern = r'(?m)^([ \t]*)(setSupplyValue\(NewShipType,\s*"([^"]+)"[^\n]*\))\s*;?[ \t]*$'
    count = 0

    def replace(match):
        nonlocal count
        count += 1
        indent, call, family = match.groups()
        if family.lower().startswith("layout") or family.lower() in RETAINED:
            return match[0]
        return (
            indent
            + "if not HWMP_CataclysmShip then\n"
            + indent
            + "    "
            + call
            + "\n"
            + indent
            + "end"
        )

    text = re.sub(pattern, replace, text)
    if count == 0:
        raise ValueError("Ship lacks supply definitions")
    value = format(cost / SCALE, ".10g")
    description = ""
    if description_key is not None:
        description = f'    NewShipType.sobDescription = "${description_key}"\n'
    return (
        text.rstrip()
        + f'\nif HWMP_CataclysmShip then\n    setSupplyValue(NewShipType, "{FAMILY}", {value})\n'
        + description
        + "end\n"
    )


def quote(text):
    return (
        '"'
        + "".join(
            chr(c) if 32 <= c < 127 and c not in (34, 92) else "\\" + format(c, "03d")
            for c in text.encode("utf8")
        )
        + '"'
    )


def generate(out):
    design = model()
    from cataclysm_descriptions import (
        description_ids,
        generate as generate_descriptions,
        patch_deathmatch,
    )

    ids = description_ids(design)
    inherited = stock_files()
    inherited.update(index(DONOR))
    # Cataclysm intentionally runs after other authoritative ship generators.
    inputs = {}

    def write(relative, text):
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="ascii", newline="\n")

    old_manifest = PROJECT / "local/cataclysm/generated.json"
    for ident, ship in design["ships"].items():
        relative = f"ship/{ident}/{ident}.ship"
        source = inherited[relative]
        before = source.read_text(encoding="utf-8-sig")
        if "local HWMP_CataclysmShip" in before:
            raise ValueError("Refusing recursive Cataclysm ship generation")
        inputs[relative] = sha(source)
        write(relative, patch_ship(before, ship["su_per_group"], ids[ident]))

    family = (DONOR / "scripts/familylist.lua").read_text(encoding="ascii")
    needle = "unitcapsFamily =\n{"
    if family.count(needle) != 1:
        raise ValueError("Unexpected native supply registry")
    family = family.replace(
        needle,
        needle + '\n    {name = "' + FAMILY + '", numParam = 1, stringParam = "Support Units"},',
        1,
    )
    write("scripts/familylist.lua", family)

    popup = (CACHE / "players-patch-audit/rm-base/ui/newui/unitcapinfopopup.lua").read_text(
        encoding="ascii"
    )
    write("ui/newui/unitcapinfopopup.lua", popup)
    taskbar = (DONOR / "ui/newui/newtaskbar.lua").read_text(encoding="ascii")
    write("ui/newui/newtaskbar.lua", taskbar)
    resource = (CACHE / "players-patch-audit/rm-base/ui/newui/resource.lua").read_text(
        encoding="ascii"
    )
    anchor = 'anchorName = "Taskbar_ResourceBottomCenter3",'
    assert resource.count(anchor) == 1
    position = resource.index("\n\t\t\t\t{", resource.index("Anchor_Spawns ="))
    resource = (
        resource[:position]
        + '\n                {anchorName="HWMP_ResourceBottomLeft", relativePos={0,1}},'
        + resource[position:]
    )
    closing = resource.rfind("\n}")
    assert closing >= 0 and "HWMP_SURow" not in resource
    row = (PROJECT / "tools/templates/cataclysm_resource_row.lua").read_text(encoding="ascii")
    resource = resource[:closing] + "\n" + row + resource[closing:]
    resource = resource.replace(
        'stylesheet = "HW2StyleSheet",',
        "stylesheet = \"HW2StyleSheet\",\n    onShow = \"UI_SetElementVisible('ResourceMenu', 'HWMP_SURow', 0)\",",
        1,
    )
    write("ui/newui/resource.lua", resource)
    from support_units_icon import generate as generate_icon

    generate_icon(out / "ui/newui/ingameicons/hwmp_support_units.tga")

    rules = (DONOR / "scripts/rules/deathmatch.lua").read_text(encoding="ascii")
    rules = re.sub(
        r"^GUID = [^\n]+",
        "GUID = { 102,45,118,10,73,244,65,193,146,224,60,78,188,165,2,45 }",
        rules,
        count=1,
        flags=re.M,
    )
    rules = re.sub(
        r"^GameRulesName = [^\n]+",
        f'GameRulesName = "HWMP {VERSION} Cataclysm"',
        rules,
        count=1,
        flags=re.M,
    )
    rules = rules.replace(
        'Race_Paths = "Deathmatch,Extras"', 'Race_Paths = "Deathmatch,Extras,HWMP_Cataclysm"'
    )
    # Four original races only; no new race objects or Dual Command aliases.
    rules = re.sub(
        r"^Race_Pass_Tags = [^\n]+",
        'Race_Pass_Tags = "race_dm,race_random"',
        rules,
        count=1,
        flags=re.M,
    )
    old = 'dofilepath("data:scripts/rules/deathmatch/deathmatch.lua")'
    if rules.count(old) != 1:
        raise ValueError("Unexpected base deathmatch entry point")
    rules = rules.replace(old, f'dofilepath("data:scripts/rules/{MODE}/{MODE}.lua")')
    write(f"scripts/rules/{MODE}.lua", rules)
    write(
        f"scripts/rules/{MODE}/props/default.lua",
        """Number_Properties_Priority = 10.0
Number_Properties = {hwmp_cataclysm = 1.0}
String_Properties_Priority = 10.0
String_Properties = {}
""",
    )
    write(
        f"scripts/rules/{MODE}/unitcaps/default.lua",
        """supplyLimit("LayoutFighter", 180)
supplyLimit("LayoutCorvette", 180)
supplyLimit("LayoutFrigate", 180)
supplyLimit("LayoutDestroyer", 180)
supplyLimit("LayoutBattleCruiser", 180)
supplyLimit("LayoutResource", 180)
supplyShow("HWMP_SupportUnits", "Never")
""",
    )
    carrier_limits = {}
    for profile, budget in design["budgets"].items():
        relative = f"scripts/rules/deathmatch/unitcaps/{profile}.lua"
        text = (DONOR / relative).read_text(encoding="ascii")
        text += f'\n-- Exact binary scale; the player-facing HUD uses ordinary SU.\nsupplyLimit("{FAMILY}", {budget / SCALE:.10g})\nsupplyShow("{FAMILY}", "Never")\n'
        # Costs of combat classes are absent in this mode; suppress empty headings.
        for category in (
            "Fighter",
            "Corvette",
            "Frigate",
            "Capital",
            "Resource",
            "Utility",
            "NonCombat",
            "Platform",
        ):
            text += f'supplyShow("{category}", "Never")\n'
        text += 'supplyShow("Carrier", "Always")\nsupplyIndent("Carrier", 0)\nsupplyShow("Shipyard", "NotEmpty")\nsupplyIndent("Shipyard", 0)\n'
        # Zero-SU probes still pay native per-type supply and keep the old caps.
        for probe_family in (
            "Probe",
            "Probe_hw1",
            "ECMProbe",
            "ProximitySensor",
            "ProximitySensor_hw1",
        ):
            text += f'supplyShow("{probe_family}", "NotEmpty")\nsupplyIndent("{probe_family}", 0)\n'
        write(f"scripts/rules/{MODE}/unitcaps/{profile}.lua", text)
        for race in design["races"]:
            # Native ordered Race_Paths composition keeps build/research/fleets and caps.
            native_path = f"scripts/races/{race}/deathmatch/unitcaps/{profile}.lua"
            native = inherited[native_path].read_text(encoding="ascii")
            write(f"scripts/races/{race}/hwmp_cataclysm/unitcaps/{profile}.lua", native)
            caps = dict(re.findall(r'supplyLimit\("([^\"]+)"\s*,\s*([0-9.]+)\)', text + native))
            carrier_limits[(race, profile)] = int(float(caps["Carrier"]))

    costs = (
        "HWMP_CataclysmCosts = {\n"
        + "".join(
            f'    ["{ident}"] = {row["su_per_group"]},\n'
            for ident, row in sorted(design["ships"].items())
        )
        + "}\n"
    )
    budgets = (
        "HWMP_CataclysmBudgets = {"
        + ",".join(f"{k}={v}" for k, v in design["budgets"].items())
        + "}\n"
    )
    write(
        "scripts/hwmp24/cataclysm_hud.lua",
        costs
        + budgets
        + (PROJECT / "tools/templates/cataclysm_hud.lua").read_text(encoding="ascii"),
    )
    write(
        f"scripts/rules/{MODE}/{MODE}.lua",
        'dofilepath("data:scripts/rules/deathmatch/deathmatch.lua")\n',
    )
    base = (DONOR / "scripts/rules/deathmatch/deathmatch.lua").read_text(encoding="ascii")
    write("scripts/rules/deathmatch/deathmatch.lua", patch_deathmatch(base))
    from cataclysm_descriptions import OWNED_NAMES

    labels = OWNED_NAMES
    for language, label in labels.items():
        write(
            f"locale/{language}/hwmp24_cataclysm.lua",
            "HWMP_CataclysmOwned = " + quote(label) + "\n",
        )

    generate_descriptions(out, design, inherited, quote)

    # Prove native crate tables cannot grant an unpriced ordinary race ship.
    for race in design["races"]:
        name = f"scripts/races/{race}/scripts/crate_ships.lua"
        content = inherited[name].read_text(encoding="ascii")
        for ident in re.findall(r'item\s*=\s*"([^"]+)"', content):
            if ident.lower() not in design["ships"]:
                raise ValueError("Unpriced crate ship: " + ident)
    save(
        old_manifest,
        {
            "version": VERSION,
            "ship_count": len(inputs),
            "source_inputs": inputs,
            "budgets": design["budgets"],
            "native_scale": SCALE,
            "carrier_bonus": False,
            "retained_families": sorted(RETAINED),
            "carrier_caps": {r + "/" + p: v for (r, p), v in carrier_limits.items()},
            "ordinary_branch_verified": False,
            "native_engine_tested": False,
            "installed": False,
        },
    )
