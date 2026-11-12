# Updating and releasing HWMP

[Русский](ru/UPDATE_WORKFLOW.md)

This procedure reproduces the base patch without rebuilding its consumers. Commands run from this repository. Use Python normally; do not disable invariant checks with `-O`. Game assets, native executables, extracted files and compiled archives remain outside Git.

## 1. Establish the input and scope

Read `AGENTS.md`, `NEXT_SESSION.md`, the acceptance checklist and the change-specific report. Record the current commit, fix revision and all release archive hashes. Preserve the previous release outside the game before replacing it.

The donor is **2.3Test build21**, SHA256 `f12e17bf9c6849599afaefa4d8281c266d637cdfc992a117ec3165891cd58f41`. `baseline/test-inventory.json` pins its extracted contents. Do not silently replace it with ordinary 2.3, merge another build or infer equivalence from a filename.

Shared fixes and original-race definitions belong here. New-race ships/research/balance belong to the next repository; scenarios/story belong to the campaign. Accepted numerical policy is 6/6 collectors and Assault last node1.2, in addition to the two documented missile corrections. A technical fix is not permission for an unrelated numerical rebalance.

## 2. Prepare native inputs

```powershell
python -m pip install -r requirements.txt
python tools/prepare_inputs.py
```

Point `HWRM_ASSET_CACHE` or ignored `local/settings.json` at your own extracted assets; see `settings.example.json`. The Toolkit's Archive.exe must be available. `prepare_inputs.py --economy` additionally extracts the Classic/regular-patch comparison inputs needed by historical audits.

The preparation validates donor hashes, native production inputs and all six language archive pins. Changed native inputs require inspection and an explicit new pin. Never commit the extracted assets or your local settings.

## 3. Change the authoritative source

`tools/hwmp24.py` assembles donor runtime files plus `hwmp-patch-2.4/overrides`. Generated overrides are regenerated on each preparation: edit their generator/template, not just the output.

- Temporary effects: `tools/templates/effects_base.lua`, `effect_journal.lua`, and `tools/effect_journal.py`. The generated effects.lua is self-contained; native Lua file scopes must not be assumed to share wrapper overrides.
- Gravity callbacks, Dock ID forwarding, transport hooks, missile fixes and accepted starts: `make_overrides()` in hwmp24.py.
- Transport state machine: the owned transport.lua override. Preserve native spawn visibility and per-owner ability baselines.
- Base times: `tools/production_data.py`, effective ship/subsystem definitions and pinned native inputs. Never hand-maintain a parallel timing table.
- New tooltip labels: `localization/hwmp24.json`. Native descriptions come from the game's own language archives, with an explicit fallback report.

Preserve upstream credit and unaffected configuration calls. For a numerical edit, compare the complete definition and prove exactly which calls changed. Do not change a display category to alter supply or infer hull count from SobGroup_Count.

## 4. Run source and Lua checks

```powershell
python tools/hwmp24.py
python tools/verify_hwmp24.py
python tools/verify_effect_journal.py
python tools/verify_installation.py
```

The verification exercises owner overlaps, mixed baseline flags/speed, transport recovery, capture identity, Dock isolation, missile selection identity, all race build tables and all language overlays. Check unknown/missing descriptions as well as normal values. Lua5.1 fixtures translate only the known Lua4 inspection syntax; they are not engine validation.

Use a **Lua4 compiler** for native files. Lua5.x accepting a mixed record/list table did not prevent an earlier native parse failure. Whitespace-only Lua cleanup must preserve tokens and still pass Lua4 parsing. Python formatting is configured in pyproject.toml; development-only formatting dependencies are separate from runtime requirements.

## 5. Diagnose in the engine

```powershell
python tools/auto_testgrounds.py
python tools/auto_testgrounds.py --install
python tools/run_auto_queue.py JournalRecycle SaveLoadEmpty SaveLoadAuto SaveLoadCold SaveLoadCoop
python tools/run_auto_pressure.py
```

Native installation/launch needs the human's request. Do not run concurrent queues or rebuild/reinstall their source while another queue has future launches. The runner refuses a pre-existing game and closes only its own terminal test process. A healthy timeout remains open. Keep full raw journals, checkpoints, process metadata and rejected pilots in ignored local/auto-tests.

For save/load, confirm a fresh owned checkpoint, actual rollback and OnStartOrLoad. A load request alone is not success. Test a new process, overlapping owners, leaving the field before the first callback, source destruction, an initially forbidden ability, and a scenario changing its allowed baseline. Check real movement after release. Preserve negative controls; do not rewrite their results as passes.

For performance, compare the same setup and clock interval before/after. Distinguish host wall time, script time, game time and FPS. The first journal prototype functioned but took about3× the stress-control time and was rejected; compact shared owner data and targeted release reduced it to about6–9% overhead in individual samples. Test long matches/network peers before generalizing.

## 6. Package and verify every archive

```powershell
python tools/hwmp24.py --package
```

The output is local/HWMPPatch24-release plus its ZIP. Every primary/language BIG is fully extracted and compared file-by-file against the intended source, not just CRC-tested. Keep the native `data` and `locale` aliases; `locale:Russian`/`locale:English` TOC aliases caused a confirmed menu regression in the consumer project.

Review `fixes.json`, local verification reports and SHA256SUMS.txt. The shared release_layout.py defines the installer/package inventory, preventing documentation additions from making the installer stale. No snapshots/examples are part of normal runtime composition. No diagnostic UI registration is added to ordinary gameplay.

After documentation-only changes, update release text, checksum list and ZIP without recompressing the validated BIGs. After runtime/localization changes, rebuild and repeat appropriate native checks. Record their exact source/fix/archive identity separately from build-only verification.

## 7. Install, accept and roll back

```powershell
python tools/install_hwmp24.py
python tools/install_hwmp24.py --install
python tools/launcher_slot.py hwmp --apply
python tools/launcher_slot.py previous --apply
```

The first command is a plan. The installer accepts only its owned folder and verifies release membership/checksums/full extraction. The selector uses the launcher's one local slot, backs up the complete previous mod outside the game and preserves the original Banana archive. Close the game/launcher yourself before switching. See LOCAL_INSTALLATION.md for paths and recovery.

Complete the field checklist with identical archives on two clients, normal/2x UI starts, physical repair evidence, UI hyperspace/cancel/guard behavior and real matches. Laboratory passes do not close those acceptance items. Old active-well saves without journal metadata are not guaranteed; consumer campaigns need their own saves and level-transition test.

## 8. Publish code, then prepare Workshop

Commit code, docs, translations, pinned hashes and frozen text examples only. Review `git diff --cached --name-only`, run checks, and push the existing branch normally; do not force-update unrelated history. GitHub contains no BIGs or raw native logs.

`tools/prepare_workshop.py` stages loose runtime files, config and the approved preview outside Git. The supplied WorkshopTool packs **loose files**, not prebuilt BIGs. Preview must satisfy its own512×512 requirement; description is limited to8000characters and title128. A new WorkshopID is0; preserve the assigned ID for later updates. See WORKSHOP.md and the installed Toolkit's ReadMe/config template.

Show the exact description and artwork before publishing. No create/update command, subscription or public listing is authorized by merely preparing this folder. After approval and upload, subscribe/test the actual Workshop artifact through the native launcher and record its hashes; Toolkit repacking is not assumed byte-identical to our local BIG.

Finally update consumer dependencies **explicitly**: base submodule and lock in the race repository, its own tests/commit; race submodule and lock in the campaign, its own tests/commit. Never auto-build, install or advance either from this base release task.
