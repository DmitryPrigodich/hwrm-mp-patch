"""Shared, campaign-independent paths, file helpers and pinned native inputs."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parents[1]
config_path = PROJECT / "local/settings.json"
SETTINGS = json.loads(config_path.read_text(encoding="utf8")) if config_path.exists() else {}
CACHE = Path(
    os.environ.get("HWRM_ASSET_CACHE") or SETTINGS.get("asset_cache") or PROJECT / "local/cache"
).resolve()
GAME = Path(SETTINGS.get("game_root", r"C:\Program Files (x86)\Steam\steamapps\common\Homeworld"))
ARCHIVE = Path(
    SETTINGS.get(
        "test_archive",
        str(GAME / "HomeworldRM/DataWorkshopMODs/76561198011852645/1413859511/2.3Test.big"),
    )
)
DONOR = CACHE / "players-patch-audit/test"
RUSSIAN_STOCK = CACHE / "hwmp-patch-2.4/russian-stock"
DONOR_SHA = "f12e17bf9c6849599afaefa4d8281c266d637cdfc992a117ec3165891cd58f41"
TOOL = Path(
    SETTINGS.get(
        "archive_tool",
        r"C:\Program Files (x86)\Steam\steamapps\common\Homeworld 347380\GBXTools\WorkshopTool\Archive.exe",
    )
)


def short_path(path):
    path = Path(path).resolve()
    if os.name != "nt":
        return str(path)
    buffer = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer)):
        raise OSError("Cannot resolve short path: " + str(path))
    return buffer.value


def build_directory(name, repository):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((str(Path(repository).resolve()) + "|" + name).encode()).hexdigest()[:10]
    target = Path(short_path(CACHE)) / "build" / key
    target.mkdir(parents=True, exist_ok=True)
    return target


def game_base():
    result = {}
    for folder in ("rm-base", "rm-hw1", "rm-hw2", "test"):
        result.update(index(CACHE / "players-patch-audit" / folder))
    return result


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8", newline="\n"
    )


def index(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_file():
            name = path.relative_to(root).as_posix().lower()
            if name in result:
                raise ValueError("Case-colliding paths: " + name)
            result[name] = path
    return result


def donor_runtime(name):
    return name not in (
        ".gitignore",
        "hwrm.lua",
        "keeper.txt",
        "readme.md",
    ) and not name.startswith("changelog/")


def copy_layer(source, destination, names=None):
    files = index(source)
    copied = []
    for name, path in sorted(files.items()):
        if names is not None and not names(name):
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(name)
    return copied
