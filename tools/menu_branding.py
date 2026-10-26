"""Pinned native front-end presentation. No new images, fonts or audio are invented."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import struct

from hwrm_common import CACHE, DONOR, GAME, PROJECT, sha
from project_credits import MENU_CREDITS

MUSIC = "data:sound/music/staging/STAGING_04"  # Inhibitors, HW2 mission4.
ASSETS = {
    "ui/newui/background/hwmp24_main_bg.tga": "rm-campaign-hw2/ui/newui/background/main_bg.tga",
    "ui/newui/background/hwmp24_wordmark.tga": "rm-base/ui/newui/background/logo.tga",
    "ui/newui/background/hwmp24_hiigaran.tga": "rm-base/badges/hiigaran.tga",
    "ui/newui/background/hwmp24_vaygr.tga": "rm-base/badges/vaygr_outline_white.tga",
    "ui/newui/background/hwmp24_taiidan.tga": "rm-base/badges/taiidan_white.tga",
}

RULE_NAMES = {
    "deathmatch.lua": "Homeworld RM - HWMP 2.4",
    "deathmatchhw1.lua": "Homeworld 1 RM - HWMP 2.4",
    "deathmatchhw2.lua": "Homeworld 2 RM - HWMP 2.4",
}


def music_metadata():
    with (GAME / "HomeworldRM/Data/Music.big").open("rb") as stream:
        header = stream.read(180)
        if header[:12] != b"_ARCHIVE\x02\0\0\0":
            raise ValueError("Unexpected native music archive format.")
        length = struct.unpack_from("<I", header, 172)[0]
        if not 24 <= length < 16 * 1024 * 1024:
            raise ValueError("Invalid music metadata size.")
        metadata = stream.read(length)
    if b"staging_04.wav\0" not in metadata.lower():
        raise ValueError("Inhibitors is absent from the shared Music.big.")
    return hashlib.sha256(metadata).hexdigest()


def hide_engine_label(text, name):
    """Retain native label names for engine callbacks, but remove their drawing/layout."""
    match = re.search(r'name\s*=\s*"' + re.escape(name) + r'"\s*,', text)
    if match is None:
        raise ValueError("Missing pinned menu label: " + name)
    position = match.end()
    next_label = text.find('type = "TextLabel"', position)
    end = next_label if next_label >= 0 else len(text)
    tail = text[position:end]
    tail = re.sub(r"\b(?:visible|ignored)\s*=\s*[01]\s*,", "", tail)
    text = text[:position] + tail + text[end:]
    # Keep a single definition of each field in the native label header.
    return (
        text[:position]
        + "\n                visible = 0,\n                ignored = 1,"
        + text[position:]
    )


def generate(overrides):
    pins = json.loads((PROJECT / "baseline/menu-inputs.json").read_text(encoding="utf8"))
    for relative, digest in pins["files"].items():
        if sha(CACHE / "players-patch-audit" / relative) != digest:
            raise ValueError("Native menu input changed: " + relative)
    if music_metadata() != pins["shared_music_metadata_sha256"]:
        raise ValueError("Native shared music inventory changed.")

    def write(name, text):
        path = overrides / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="ascii", newline="\n")

    menu = (DONOR / "ui/newui/main/newmainmenu.lua").read_text(encoding="ascii")
    for name in ("lblBuildNumber", "lblVersion"):
        menu = hide_engine_label(menu, name)
    credits = (PROJECT / "tools/templates/menu_credits.lua").read_text(encoding="ascii")
    if credits.count("__HWMP_CREDITS__") != 1 or not menu.rstrip().endswith("\n}"):
        raise ValueError("Pinned menu/credits template structure changed.")
    credits = credits.replace("__HWMP_CREDITS__", json.dumps(MENU_CREDITS))
    closing = menu.rfind("\n}")
    menu = menu[:closing] + "\n" + credits.rstrip() + menu[closing:]
    write("ui/newui/main/newmainmenu.lua", menu)
    write("playerspatch_buildnumber.lua", 'PlayersPatchBuildNumber = "HWMP 2.4"\n')
    for filename, title in RULE_NAMES.items():
        relative = "scripts/rules/" + filename
        rules = (DONOR / relative).read_text(encoding="ascii")
        rules, count = re.subn(
            r'(?m)^(GameRulesName\s*=\s*)"[^"\r\n]*"',
            lambda match: match[1] + '"' + title + '"',
            rules,
        )
        if count != 1:
            raise ValueError("Expected one native game-type title: " + filename)
        # Display name only: preserve GUID, filters, save version and options.
        write(relative, rules)
    write(
        "ui/newui/background/logo.lua",
        (PROJECT / "tools/templates/menu_logo.lua").read_text(encoding="ascii"),
    )
    background = (CACHE / "players-patch-audit/rm-base/ui/newui/main/background.lua").read_text(
        encoding="ascii"
    )
    old = "Background\\\\main_bg.tga"
    if background.count(old) != 1:
        raise ValueError("Native menu background binding changed.")
    write(
        "ui/newui/main/background.lua", background.replace(old, "Background\\\\hwmp24_main_bg.tga")
    )
    config = (CACHE / "players-patch-audit/rm-base/soundscripts/soundconfig.lua").read_text(
        encoding="ascii"
    )
    config, count = re.subn(r'(?m)^FEMusic\s*=\s*"[^"\n]+"', 'FEMusic = "' + MUSIC + '"', config)
    if count != 1:
        raise ValueError("Expected one native front-end music binding.")
    write("soundscripts/soundconfig.lua", config)
    for target, source in ASSETS.items():
        path = overrides / target
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CACHE / "players-patch-audit" / source, path)
