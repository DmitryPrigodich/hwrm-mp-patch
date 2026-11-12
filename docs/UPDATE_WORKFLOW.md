# Update and release workflow

[Русский](ru/UPDATE_WORKFLOW.md)

The current candidate is 2.4.6 without SU. Read AGENTS.md, NEXT_SESSION.md, [review changes](REVIEW_2_4_6.md) and [acceptance](CLOSURE_CHECKLIST.md). Preserve the pinned Test21 and six native language inputs. Code/assets remain separate; never build downstream automatically.

## Source and offline checks

```powershell
python -m pip install -r requirements-dev.txt
python -m black --check tools tests
python -m pyflakes tools tests
python -m unittest discover -s tests -v
```

All active tools reject optimized Python before work. Critical source pins/path guards also use explicit exceptions. Edit hand-maintained files listed in `hwmp-patch-2.4/manual-files.json`, generators and `tools/templates/effects.lua`. Generated outputs live under the selected build's ignored `generated/` directory and must not be edited. The merged effect template preserves the previously generated Lua bytes.

## Candidate build

```powershell
python tools/prepare_inputs.py
python tools/hwmp24.py --package --candidate
python tools/install_hwmp24.py --candidate
```

Output: `local/HWMPPatch246-candidate`; work/receipts: `local/builds/2.4.6/candidate`. Omit `--candidate` for the independent ordinary output `local/HWMPPatch246-release` and work path. Both modes use explicit build contexts. Fresh staging excludes stale files; promotion preserves the previous owned directory and rolls back a failed replacement. A portable `verification-package.json` travels inside each release, so later builds cannot stale another package's receipt. All seven BIGs are fully extracted and compared.

## Installation and native acceptance

The installer command above only prints a plan. After an explicit owner request and closed game/launcher, add `--install`. Never stop the human's game. [Installation](LOCAL_INSTALLATION.md). Record the exact package hashes for native tests; mocks/CRC do not prove engine behavior. SU must remain excluded unless a separate future implementation passes native accounting and queue acceptance.

## Publication

No upload is implied by building. Review exact EN/RU descriptions and cover, obtain the owner's publication instruction, then update existing item 3827773780. Staging uses the selected explicit build context and verifies its matching manifest. Verify the actual downloaded Workshop payload separately. Published 2.4.5 receipts and prior source remain historical evidence; no downstream pin/build advances automatically.
