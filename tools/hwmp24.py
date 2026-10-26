"""HWMP Patch 2.4: independent Test-derived general fixes and original races.

Only project-local preparation/package operations. No install, game or launcher.
"""

from __future__ import annotations
from project_credits import SHORT_CREDITS
from project_version import TITLE, VERSION
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from hwrm_common import (
    PROJECT,
    CACHE,
    DONOR,
    ARCHIVE,
    DONOR_SHA,
    RUSSIAN_STOCK,
    sha,
    index,
    save,
    copy_layer,
    donor_runtime,
    build_directory,
)

ROOT = PROJECT / "hwmp-patch-2.4"
WORK = PROJECT / "local/hwmp-patch-2.4"
BUILD = build_directory("hwmp24", PROJECT)
SOURCE = BUILD / "source"
RELEASE = PROJECT / "local/HWMPPatch24-release"
IDENTITY = "HWMP-Patch-2.4-dev1"
START_FLEET_INPUTS = (
    ("vaygr00.lua", "rm-base", "8e22ba6545d98a62e611ee2533bd5068201d0640843939696177d45a9a852b30"),
    ("2x_vaygr00.lua", "test", "410f75fde0724cc5fc52a90dfb8177961cfa64e1935a4b500e2c742d99a98d8a"),
)


def equal_collector_start(text):
    # Only the resource-collector entry changes; preserve every other field.
    pattern = r'(type\s*=\s*"Vgr_ResourceCollector",[\s\S]*?\bnumber\s*=\s*)7(?=\s*,)'
    result, n = re.subn(pattern, lambda m: m[1] + "6", text)
    assert n == 1, "Expected exactly one seven-collector Vaygr entry"
    return result


def write(root, name, text):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="ascii", newline="\n")


def replace_function(text, name, replacement):
    pattern = r"^function " + re.escape(name) + r"\([^\n]*\).*?(?=^function |\Z)"
    result, n = re.subn(pattern, lambda _: replacement + "\n\n", text, count=1, flags=re.M | re.S)
    assert n == 1, name
    return result


SPLIT = """function SobGroup_Split(group, granularity)
    granularity = granularity or 1
    if granularity < 1 then granularity = 1 end
    local result = {}
    for i = 0, SobGroup_Count(group) - 1, granularity do
        local subgroup = SobGroup_Fresh(group .. "-subgroup-" .. i)
        SobGroup_FillShipsByIndexRange(subgroup, group, i, granularity)
        if SobGroup_Empty(subgroup) == 0 then result[getn(result) + 1] = subgroup end
    end
    return result
end"""

SCUTTLE = """-- Native capture disables Scuttle before the first towing callback.
HWMP_SalvageStates = HWMP_SalvageStates or {}
function SobGroup_NoSalvageScuttle(group, player_index, ship_id)
    local owner = "salvage:" .. (ship_id or group)
    if SobGroup_Empty(group) == 1 then
        HWMP_ReleaseOwner(owner)
        if ship_id ~= nil then HWMP_SalvageStates[ship_id] = nil end
        return
    end
    local docking = SobGroup_IsDoingAbility(group, AB_Dock)
    -- Legacy callers without a stable hull ID retain the immediate contract.
    if ship_id == nil then
        if docking == 1 then HWMP_BlockGroup(group, owner, { AB_Scuttle }, 0)
        else HWMP_ReleaseOwner(owner) end
        return
    end
    local state = HWMP_SalvageStates[ship_id]
    if state == nil then state = {}; HWMP_SalvageStates[ship_id] = state end
    local record = HWMP_FindEffectRecord(group, 0)
    local saved = nil
    if record and record.abilities[AB_Scuttle] then saved = record.abilities[AB_Scuttle].baseline end
    if docking == 1 then
        local baseline = saved or state.allowed
        HWMP_BlockGroup(group, owner, { AB_Scuttle }, 0)
        if state.active ~= 1 and baseline ~= nil then
            -- CanDoAbility also includes native Dock eligibility. Set the baseline
            -- after the effect record exists; enabling alone cannot bypass that gate.
            HWMP_SetAbilityAllowed(group, AB_Scuttle, baseline)
        end
        record = HWMP_FindEffectRecord(group, 0)
        state.allowed = record.abilities[AB_Scuttle].baseline
        state.active = 1
    else
        if state.active == 1 then
            -- Cooperative baseline changes take precedence over the earlier snapshot.
            if saved ~= nil then state.allowed = saved end
            HWMP_ReleaseOwner(owner)
            -- Capture can remove old group membership while preserving native shipID.
            if state.allowed ~= nil then HWMP_SetAbilityAllowed(group, AB_Scuttle, state.allowed) end
            state.active = nil
        end
        record = HWMP_FindEffectRecord(group, 0)
        if record and record.abilities[AB_Scuttle] then state.allowed = record.abilities[AB_Scuttle].baseline
        else state.allowed = SobGroup_CanDoAbility(group, AB_Scuttle) end
    end
end"""

DOCK = """HWMP_DockStalls = HWMP_DockStalls or {}
function SobGroup_UnderAttackReissueDock(group, ship_id)
    local key = ship_id or group
    if SobGroup_GetCurrentOrder(group) ~= COMMAND_Dock or SobGroup_IsDocked(group) == 1 or
       SobGroup_UnderAttack(group) ~= 1 or SobGroup_CanDoAbility(group, AB_Dock) ~= 1 or
       SobGroup_CanDoAbility(group, AB_Move) ~= 1 then
        HWMP_DockStalls[key] = nil
        return
    end
    local now = Universe_GameTime()
    if SobGroup_GetActualSpeed(group) >= 1 then HWMP_DockStalls[key] = nil; return end
    local state = HWMP_DockStalls[key]
    if state == nil then state = { since = now, retry = -100 }; HWMP_DockStalls[key] = state end
    if now - state.since >= 3 and now - state.retry >= 5 then
        SobGroup_DockSobGroupWithAny(group)
        state.retry = now
        state.since = now
    end
end"""

BUILD_TIMES = """-- HWMP2.4: selected-language text; unknown descriptions retain their UCS ID.
doscanpath("data:ui", "playerspatch_ui_util.lua")
if GetProductionTimeSetting() == 2 then
    dofilepath("data:scripts/hwmp24/tooltips.lua")
    dofilepath("data:scripts/productiontimes/buildtimes.lua")
    for i, item in build do
        local seconds = buildtimes[item.ThingToBuild]
        local description = HWMP_TooltipText(item.Description)
        if seconds ~= nil and description ~= nil and description ~= "" then
            build[i].Description = description .. "  \\n\\n<b>" .. HWMP_TooltipBaseTime() .. ":</b>  " .. seconds .. HWMP_TooltipSecondsLabel
        end
    end
end
"""

RESEARCH_TIMES = """-- HWMP2.4: do not replace localized text with a forced English dictionary.
doscanpath("data:ui", "playerspatch_ui_util.lua")
if GetProductionTimeSetting() == 2 then
    dofilepath("data:scripts/hwmp24/tooltips.lua")
    for i, item in research do
        local description = HWMP_TooltipText(item.Description)
        if description ~= nil and description ~= "" and item.Time ~= nil then
            local value = ""
            if item.UpgradeValue ~= nil then
                local percent = item.UpgradeValue * 100 - 100
                local sign = ""
                if percent > 0 then sign = "+" end
                value = "\\n<b>" .. HWMP_TooltipValue() .. ":</b> " .. sign .. percent .. "% "
            end
            research[i].Description = description .. "  \\n" .. value .. "\\n<b>" .. HWMP_TooltipBaseTime() .. ":</b> " .. item.Time .. HWMP_TooltipSecondsLabel
        end
    end
end
"""


def lua_quote(value):
    result = '"'
    for c in value.encode("utf8"):
        if c in (34, 92):
            result += "\\" + chr(c)
        elif c < 32 or c >= 127:
            result += "\\" + format(c, "03d")
        else:
            result += chr(c)
    return result + '"'


def locale_tables():
    from language_data import generate

    return generate(ROOT / "overrides", lua_quote)


def make_overrides():
    out = ROOT / "overrides"
    from effect_journal import generate_effects, patch_gravity
    from menu_branding import generate as generate_menu

    generate_menu(out)

    write(out, "scripts/hwmp24/effects.lua", generate_effects())
    # Approved 25 October after native clean-income tests: equal six-collector starts.
    # Carrier/full-fleet starts already have six; empty starts stay empty.
    for filename, folder, digest in START_FLEET_INPUTS:
        name = "scripts/startingfleets/" + filename
        source = CACHE / "players-patch-audit" / folder / name
        assert sha(source) == digest, name
        write(out, name, equal_collector_start(source.read_text(encoding="ascii")))
    core = (DONOR / "scripts/playerspatch/ships_util/core/global.lua").read_text()
    core = 'dofilepath("data:scripts/hwmp24/effects.lua")\n' + core
    core = replace_function(core, "SobGroup_Split", SPLIT)
    core = replace_function(core, "SobGroup_NoSalvageScuttle", SCUTTLE)
    core = replace_function(core, "SobGroup_UnderAttackReissueDock", DOCK)
    dock_ships = (
        "hgn_assaultcorvette",
        "hgn_attackbomber",
        "hgn_pulsarcorvette",
        "hgn_interceptor",
        "hgn_scout",
        "vgr_bomber",
        "vgr_lancefighter",
        "vgr_missilecorvette",
        "vgr_scout",
        "vgr_interceptor",
        "vgr_lasercorvette",
    )
    for ship in dock_ships:
        name = f"ship/{ship}/{ship}.lua"
        text = (DONOR / name).read_text()
        old = "SobGroup_UnderAttackReissueDock(CustomGroup)"
        assert text.count(old) == 1, name
        write(out, name, text.replace(old, "SobGroup_UnderAttackReissueDock(CustomGroup, shipID)"))

    core = core.replace(
        "SobGroup_CreateIfNotExist(all_ships)\n",
        "SobGroup_CreateIfNotExist(all_ships)\n\tSobGroup_Clear(all_ships)\n",
        1,
    )
    core = core.replace("if (Player_IsAlive(i)) then", "if (Player_IsAlive(i) == 1) then", 1)
    write(out, "scripts/playerspatch/ships_util/core/global.lua", core)
    name = "scripts/playerspatch/ships_util/lib/gravwells.lua"
    text = (DONOR / name).read_text()
    start = text.index("\tfunction GRAVWELL_PROTO:StunGroup")
    end = text.index("\n\t-- tumbles", start)
    text = text[:start] + """    function GRAVWELL_PROTO:StunGroup(group, stunned)
        local owner = "gravwell:" .. self.ship_id
        if stunned == 0 then HWMP_UnblockGroup(group, owner)
        else HWMP_BlockGroup(group, owner, GW_MEM_PROTO.abilities_to_disable, 1) end
    end
""" + text[end:]
    text = text.replace(
        "SobGroup_ClearTumble(group);",
        'HWMP_ClearReleasedTumble(group, "gravwell:" .. self.ship_id);',
    )
    text = text.replace(
        "SobGroup_AbilityActivate(this_gravwell.own_group, AB_Hyperspace, 0)",
        'HWMP_BlockGroup(this_gravwell.own_group, "gravwell-self:" .. ship_id, { AB_Hyperspace }, 0)',
    )
    text = text.replace(
        "SobGroup_AbilityActivate(group, AB_Hyperspace, 1);",
        'HWMP_ReleaseOwner("gravwell-self:" .. ship_id);\n    HWMP_ReleaseOwner("gravwell:" .. ship_id);',
    )
    anchor = "function GW_MEM:Destroy(group, player_index, ship_id)"
    text = text.replace(
        anchor,
        anchor
        + '\n    HWMP_ReleaseOwner("gravwell:" .. ship_id)\n    HWMP_ReleaseOwner("gravwell-self:" .. ship_id)',
        1,
    )
    text = re.sub(r"\bprint\(", "HWMP_Log(", text)
    text += """
-- New mods register additional valid hull IDs without editing the core list.
function HWMP_RegisterGravityTarget(ship_type)
    for i = 1, getn(GW_MEM_PROTO.target_types) do
        if GW_MEM_PROTO.target_types[i] == ship_type then return end
    end
    GW_MEM_PROTO.target_types[getn(GW_MEM_PROTO.target_types) + 1] = ship_type
end
"""
    write(out, name, patch_gravity(text))
    name = "scripts/playerspatch/ships_util/lib/frigates.lua"
    text = (DONOR / name).read_text()
    text = replace_function(
        text, "SupportFrigate_HyperspaceDock", 'dofilepath("data:scripts/hwmp24/transport.lua")'
    )
    write(out, name, text)
    for prefix, label in (("kus", "Kus"), ("tai", "Tai")):
        name = f"ship/{prefix}_supportfrigate/{prefix}_supportfrigate.lua"
        text = (DONOR / name).read_text()
        create = f"function Create_{label}_SupportFrigate(CustomGroup, playerIndex, shipID)"
        assert text.count(create) == 1
        text = text.replace(create, create + "\n    HWMP_TransportRemember(CustomGroup, shipID)", 1)
        text = replace_function(
            text,
            f"Destroy_{label}_SupportFrigate",
            f"function Destroy_{label}_SupportFrigate(CustomGroup, playerIndex, shipID)\n    HWMP_TransportDestroy(CustomGroup, shipID)\nend",
        )
        write(out, name, text)
    name = "ship/tai_defensefighter/tai_defensefighter.lua"
    text = (DONOR / name).read_text()
    start = text.index("    if (defenseFighterMissileTargets[shipID] ~= numberEnemyMissiles) then")
    end = text.index("    return incomingEnemyMissiles", start)
    text = (
        text[:start]
        + """    -- Refresh at the existing 1.25s unit callback cadence. A count is not a target identity.
    defenseFighterMissileTargets[shipID] = incomingEnemyMissiles
    SobGroup_AttackSelection(playerID, CustomGroup, "IncomingMissiles", 1)

"""
        + text[end:]
    )
    # Keep the guard target across the missile attack (which has no ship target).
    text = replace_function(
        text,
        "updateDefenseFighterDefense",
        """function updateDefenseFighterDefense(CustomGroup, playerID, shipID)
    local guard = "DefenseFighterGuardTargets" .. shipID
    local current = "defenseFighterGuardCurrent"
    SobGroup_CreateIfNotExist(guard)
    SobGroup_CreateIfNotExist(current)
    SobGroup_Clear(current)
    SobGroup_GetCommandTargets(current, CustomGroup, COMMAND_Guard)
    if SobGroup_Empty(current) == 0 then SobGroup_Copy(guard, current) end
    findAndAttackEnemyMissiles(CustomGroup, playerID, shipID)
end""",
    )
    text = replace_function(
        text,
        "updateDefenseFighterAttack",
        """function updateDefenseFighterAttack(CustomGroup, playerID, shipID)
    -- Missile selections need not appear in SobGroup_GetCommandTargets.
    if findAndAttackEnemyMissiles(CustomGroup, playerID, shipID) > 0 then return end
    local guard = "DefenseFighterGuardTargets" .. shipID
    SobGroup_CreateIfNotExist(guard)
    if SobGroup_Empty(guard) == 0 then
        SobGroup_GuardSobGroup(CustomGroup, guard)
        SobGroup_Clear(guard)
    end
end""",
    )
    text = "defenseFighterMissileTargets = defenseFighterMissileTargets or {}\n" + text
    write(out, name, text)
    # PR23: both platform launchers should use the stated 5500 range.
    name = "weapon/vgr_heavyfusionmissilelauncherturret/vgr_heavyfusionmissilelauncherturret.wepn"
    text = (DONOR / name).read_text(encoding="utf-8-sig")
    old = '"Normal",40,6000,0,0,0,0,1,0,1,15,'
    assert text.count(old) == 1
    write(out, name, text.replace(old, '"Normal",40,5500,0,0,0,0,1,0,1,15,'))
    # PR20 explicitly selects 0.85; remove the conflicting earlier 0.8 entry.
    name = "weapon/vgr_concussionmissilelauncher/vgr_concussionmissilelauncher.wepn"
    text = (DONOR / name).read_text(encoding="utf-8-sig")
    assert text.count("{SuperUtilityArmour = 0.8},\n") == 1
    assert text.count("{SuperUtilityArmour = 0.85}") == 1
    write(out, name, text.replace("{SuperUtilityArmour = 0.8},\n", ""))
    # Approved 25 October: smooth the Assault's last speed-accuracy node only.
    for suffix in ("bottom", "left", "right"):
        weapon = "vgr_flechettecannonassaultfrigate" + suffix
        name = f"weapon/{weapon}/{weapon}.wepn"
        text = (DONOR / name).read_text(encoding="ascii")
        old = "487, 1.2, 535, 4.0);"
        assert text.count(old) == 1
        write(out, name, text.replace(old, "487, 1.2, 535, 1.2);"))
    # Test21 omitted the weapon-fire binding for its Medium missile resource.
    default_name = "scripts/races/vaygr/scripts/research/default.lua"
    default = (DONOR / default_name).read_text(encoding="ascii")
    default, n = re.subn(
        r'(?m)^(\s*Name\s*=\s*)"Scout speed limiter"', r'\1"ScoutSpeedLimiter"', default
    )
    assert n == 1
    write(out, default_name, default)
    wf_source = (
        CACHE
        / "players-patch-audit/rm-base/scripts/weaponfire/vgr_heavymissile/vgr_heavymissile.wf"
    )
    assert sha(wf_source) == "3471396674ab2458e33bedb24d766b5baebeb8def303a25a0b22872698350f65"
    wf = wf_source.read_text(encoding="ascii")
    assert wf.count('scartype = "Vgr_HeavyMissile/Vgr_HeavyMissile"') == 1
    write(
        out,
        "scripts/weaponfire/vgr_mediummissile/vgr_mediummissile.wf",
        wf.replace(
            'scartype = "Vgr_HeavyMissile/Vgr_HeavyMissile"',
            'scartype = "Vgr_MediumMissile/Vgr_MediumMissile"',
        ),
    )
    write(out, "scripts/productiontimes/applybuildtimes.lua", BUILD_TIMES)
    write(out, "scripts/productiontimes/applyresearchtimes.lua", RESEARCH_TIMES)
    from production_data import generate

    generate()
    locale_tables()


def prepare():
    assert sha(ARCHIVE) == DONOR_SHA, "Pinned Test changed."
    inventory = json.loads((PROJECT / "baseline/test-inventory.json").read_text(encoding="utf8"))[
        "inventory"
    ]
    expected = {row["path"]: row["sha256"] for row in inventory if row["patch"] == "test"}
    assert {
        name: sha(path) for name, path in index(DONOR).items()
    } == expected, "Donor extraction changed."
    from stock_assets import validate_inputs, generate_aliases, content_revision

    stock_assets = validate_inputs()
    make_overrides()
    generate_aliases(ROOT / "overrides", stock_assets)
    SOURCE.mkdir(parents=True, exist_ok=True)
    marker = SOURCE / "hwmp24-id.txt"
    if any(SOURCE.iterdir()):
        assert marker.is_file() and marker.read_text().strip() == IDENTITY
        assert SOURCE.resolve().is_relative_to(BUILD.resolve())
        shutil.rmtree(SOURCE)
        SOURCE.mkdir()
    write(SOURCE, "hwmp24-id.txt", IDENTITY + "\n")
    omitted = {row["path"] for row in stock_assets["assets"]}
    names = copy_layer(DONOR, SOURCE, lambda name: donor_runtime(name) and name not in omitted)
    for name, path in index(SOURCE).items():
        if path.stat().st_size == 0 and path.suffix == ".lua":
            write(SOURCE, name, "-- Intentionally empty upstream Lua file.\n")
    overrides = copy_layer(ROOT / "overrides", SOURCE)
    files = {name: sha(path) for name, path in index(SOURCE).items()}
    fix_hashes = {name: sha(path) for name, path in index(ROOT / "overrides").items()}
    revision = (
        __import__("hashlib").sha256(json.dumps(fix_hashes, sort_keys=True).encode()).hexdigest()
    )
    report = {
        "identity": IDENTITY,
        "source": str(SOURCE),
        "base_sha256": DONOR_SHA,
        "base_runtime_files": names,
        "overrides": fix_hashes,
        "fix_revision": revision,
        "content_revision": content_revision(files),
        "stock_asset_fallbacks": stock_assets,
        "version": VERSION,
        "files": files,
        "engine_tested": False,
        "installed": False,
    }
    save(WORK / "manifest.json", report)
    save(
        ROOT / "fixes.json",
        {
            "identity": IDENTITY,
            "base_sha256": DONOR_SHA,
            "fix_revision": revision,
            "content_revision": report["content_revision"],
            "stock_asset_fallbacks": stock_assets,
            "version": VERSION,
            "overrides": fix_hashes,
        },
    )
    print(
        json.dumps(
            {
                "hwmp24_source": str(SOURCE),
                "files": len(files),
                "fix_files": len(overrides),
                "fix_revision": revision,
            }
        )
    )
    return report


def package():
    import hwrm_archive as builder
    from hwrm_common import short_path
    from verify_hwmp24 import verify_source, verify_archive

    report = prepare()
    verify_source()
    RELEASE.mkdir(parents=True, exist_ok=True)
    output = RELEASE / "HWMPPatch24.big"
    oldroot = builder.ROOT
    builder.ROOT = SOURCE
    short = short_path(SOURCE)
    data = [
        short + "\\" + str(path.relative_to(SOURCE))
        for name, path in sorted(index(SOURCE).items())
        if not name.startswith("locale/")
    ]
    lines = [
        f'Archive name="{TITLE}"',
        'TOCStart name="HWMP24Data" alias="data" relativeroot=""',
        'FileSettingsStart defcompression="2"',
        "FileSettingsEnd",
        *data,
        "TOCEnd",
        *builder.locale_toc("English", "HWMP24Locale", short),
        "",
    ]
    manifest = WORK / "HWMPPatch24.archive.txt"
    manifest.write_text("\r\n".join(lines), encoding="ascii", newline="")
    builder.archive(manifest, output)
    from language_data import LANGUAGES

    for language in LANGUAGES:
        manifest = WORK / (language + ".archive.txt")
        manifest.write_text(
            "\r\n".join(
                [
                    'Archive name="' + TITLE + " " + language + '"',
                    *builder.locale_toc(language, "HWMP24" + language, short),
                    "",
                ]
            ),
            encoding="ascii",
            newline="",
        )
        builder.archive(manifest, RELEASE / (language + ".big"))
    builder.ROOT = oldroot
    verify_archive(output)
    for path in RELEASE.glob("*.log"):
        shutil.move(str(path), str(WORK / path.name))
    shutil.copy2(ROOT / "README.md", RELEASE / "README.md")
    from release_layout import RELEASE_DOCS, RELEASE_RUSSIAN_DOCS

    shutil.copy2(ROOT / "readme.ru.md", RELEASE / "README.ru.md")
    for name in RELEASE_DOCS:
        shutil.copy2(PROJECT / "docs" / name, RELEASE / name)
    for name in RELEASE_RUSSIAN_DOCS:
        shutil.copy2(PROJECT / "docs/ru" / name, RELEASE / name.replace(".md", ".ru.md"))
    (RELEASE / "config.txt").write_text(
        f"Title: {TITLE}\n\nTags: Balance Fixes Multiplayer\nGameType: HomeworldRM\nModType: MOD\nBigFilename: HWMPPatch24.big\n\nDescription:\nTest21-based multiplayer fixes and scoped balance improvements.\n"
        + SHORT_CREDITS
        + "\n",
        encoding="ascii",
    )
    for name in ("start_hwmp_patch.ps1", "HWMP Patch 2.4.cmd"):
        shutil.copy2(ROOT / name, RELEASE / name)
    shutil.copy2(ROOT / "fixes.json", RELEASE / "version.json")
    sums = {p.name: sha(p) for p in RELEASE.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt"}
    (RELEASE / "SHA256SUMS.txt").write_text(
        "".join(v + "  " + k + "\n" for k, v in sorted(sums.items())), encoding="ascii"
    )
    with zipfile.ZipFile(RELEASE.with_suffix(".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for p in RELEASE.iterdir():
            if p.is_file():
                z.write(p, RELEASE.name + "/" + p.name)
    result = {
        "identity": IDENTITY,
        "release": str(RELEASE),
        "main_sha256": sha(output),
        "main_bytes": output.stat().st_size,
        "fix_revision": report["fix_revision"],
        "content_revision": report["content_revision"],
        "installed": False,
        "engine_tested": False,
    }
    save(WORK / "release.json", result)
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--package", action="store_true")
    args = p.parse_args()
    if args.package:
        package()
    else:
        prepare()
