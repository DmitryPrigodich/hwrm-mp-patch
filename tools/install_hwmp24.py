"""Install the verified standalone release in its own folder; never launch.

Default is a read-only plan. --install is an explicit filesystem operation.
The native launcher enumerates Steam subscriptions and the Banana slot only;
this installer deliberately leaves that occupied slot alone.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from hwrm_common import GAME, PROJECT, index, save, sha
from hwmp24 import IDENTITY, RELEASE, WORK

MARKER = 'package-id.txt'
PAYLOAD = {'HWMPPatch24.big', 'English.big', 'Russian.big', 'config.txt',
           'README.md', 'NATIVE_TESTS.md', 'version.json',
           'HWMP Patch 2.4.cmd', 'start_hwmp_patch.ps1'}


def release_files():
    sums = {}
    for line in (RELEASE/'SHA256SUMS.txt').read_text(encoding='ascii').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([^/\\]+)', line)
        if not match or match[2] in sums:
            raise ValueError('Invalid release checksum list.')
        sums[match[2]] = match[1]
    if set(sums) != PAYLOAD:
        raise ValueError('Unexpected release files: '+repr(set(sums)^PAYLOAD))
    if {p.name for p in RELEASE.iterdir()} != PAYLOAD | {'SHA256SUMS.txt'}:
        raise ValueError('Unexpected release directory contents.')
    for name, digest in sums.items():
        if sha(RELEASE/name) != digest:
            raise ValueError('Release checksum mismatch: '+name)
    version = json.loads((RELEASE/'version.json').read_text(encoding='utf8'))
    if version['identity'] != IDENTITY:
        raise ValueError('Wrong package identity.')
    verified = json.loads((WORK/'verification-package.json').read_text(encoding='utf8'))
    verified_sums = {Path(a['archive']).name: a['sha256'] for a in verified['archives']}
    if verified['status'] != 'passed' or not verified['full_extract_hash_comparison']:
        raise ValueError('Full archive verification is required.')
    for name in ('HWMPPatch24.big', 'English.big', 'Russian.big'):
        if verified_sums.get(name) != sums[name]:
            raise ValueError('Archive verification is stale: '+name)
    return {**sums, 'SHA256SUMS.txt': sha(RELEASE/'SHA256SUMS.txt')}, version


def other_mod_files(root, target):
    # Metadata inventory of every other mod. No files are opened or changed.
    return {p.relative_to(root).as_posix(): [p.stat().st_size, p.stat().st_mtime_ns]
            for p in root.rglob('*') if p.is_file() and not p.is_relative_to(target)}


def active_processes(game):
    script = "Get-Process -Name HomeworldRM,Launcher -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path | ConvertTo-Json -Compress"
    proc = subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], capture_output=True, text=True)
    # Get-Process returns nonzero when some names are absent; use returned JSON.
    rows = json.loads(proc.stdout) if proc.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    return [p for p in rows if p['ProcessName'] == 'HomeworldRM' or
            (p.get('Path') and Path(p['Path']).resolve().is_relative_to(game))]


def install(game_root=GAME, apply=False):
    game = Path(game_root).resolve()
    mods = (game/'HomeworldRM/DataWorkshopMODs').resolve(strict=True)
    target = (mods/'HWMPPatch24').resolve()
    if target.parent != mods or target.name != 'HWMPPatch24' or target.is_symlink():
        raise ValueError('Unsafe installation target.')
    sums, version = release_files()
    if target.exists():
        if not (target/MARKER).is_file() or (target/MARKER).read_text().strip() != IDENTITY:
            raise ValueError('Existing folder is not an owned HWMP24 installation: '+str(target))
        if set(index(target)) - {n.lower() for n in PAYLOAD | {MARKER, 'SHA256SUMS.txt'}}:
            raise ValueError('Existing folder has unowned files; preserve them before updating.')
        if any(p.is_symlink() or p.is_junction() for p in target.rglob('*')):
            raise ValueError('Links are not allowed inside the installed package.')
    result = {'identity': IDENTITY, 'target': str(target), 'files': sums,
              'fix_revision': version['fix_revision'], 'installed': False,
              'launched': False, 'engine_tested': False,
              'launcher_registration': 'Direct CMD only; occupied Banana slot unchanged.'}
    if not apply:
        return result
    running = active_processes(game)
    if running:
        raise RuntimeError('Close the game/launcher yourself before installation: '+repr(running))
    before = other_mod_files(mods, target)
    protected = [game/relative for relative in (
        'HomeworldRM/Data/BananaDLC.big',
        'HomeworldRM/DataWorkshopMODs/Gearbox/BananaMothership/BananaDLC.big',
        'HomeworldRM/DataWorkshopMODs/Gearbox/BananaMothership/VastReachesMiniCampaign.big',
        'HomeworldRM/DataWorkshopMODs/Gearbox/BananaMothership/config.txt',
        'HomeworldRM/DataWorkshopMODs/VastReachesMiniCampaign/VastReachesMiniCampaign.big',
        'HomeworldRM/DataWorkshopMODs/76561198011852645/1413859511/2.3Test.big',
        'HomeworldRM/DataWorkshopMODs/76561198011852645/1190476337/2.3PlayersPatch.big')]
    guard = {str(p): sha(p) for p in protected if p.is_file()}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = PROJECT/'local/installed-backups'/stamp/'HWMPPatch24'
    if target.exists():
        shutil.copytree(target, backup)
        assert {n: sha(p) for n,p in index(target).items()} == {n: sha(p) for n,p in index(backup).items()}
        result['backup'] = str(backup)
    target.mkdir(exist_ok=True)
    for name in sums:
        temporary = target/('.hwmp24-'+name)
        if temporary.exists():
            raise ValueError('Unexpected staging file: '+str(temporary))
        shutil.copy2(RELEASE/name, temporary)
        assert sha(temporary) == sums[name]
        temporary.replace(target/name)
    (target/MARKER).write_text(IDENTITY+'\n', encoding='ascii')
    assert {n: sha(target/n) for n in sums} == sums
    assert other_mod_files(mods, target) == before, 'Other mod files changed during installation.'
    assert {name: sha(Path(name)) for name in guard} == guard, 'Protected game package changed.'
    result.update(installed=True, installed_at_utc=stamp, protected_hashes=guard,
                  other_mods_unchanged=True)
    save(PROJECT/'local/installation.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--game-root', type=Path, default=GAME)
    args = parser.parse_args()
    print(json.dumps(install(args.game_root, args.install), ensure_ascii=False, indent=2))
