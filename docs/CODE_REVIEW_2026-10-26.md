# Release review — 26 October 2026

[Русский](ru/CODE_REVIEW_2026-10-26.md)

## Delivered

- English primary README/current documents and separate Russian README/docs. Historical detailed Russian evidence preserved.
- Fixed stale installer payload by sharing release_layout.py with packaging; verified every archive, ownership/refusal paths, backup hashes and unrelated-file preservation.
- Reversible native-launcher selector with full outside-game backups, current-state verification and injected-copy-failure rollback tests. Actual HWMP→VR→HWMP roundtrip also passed; the slot is left on HWMP. The installed native32-bit parser accepts the title/type/main BIG. No launcher window or normal gameplay was started for that parser check.
- Streamed1MiB SHA256 hashing instead of allocating complete BIG files. Existing timing/gameplay coefficients preserved.
- All51Python tools formatted with Black26.10.1/AST equivalence; effect Lua4 templates expanded without changing code tokens. Generated effects.lua also matches the previous tested commit's non-comment token stream exactly. All32override Lua files passed Lua4 parsing.
- Six native tooltip dictionaries:1354nonempty descriptions each, zero nonempty English fallbacks; two intentionally empty reserved IDs1808/1809 remain empty. Three added labels per language. All four build tables/6languages pass source fixtures; fonts/wrapping/native UI still need players.
- Frozen text-only examples:73files with manifest hashes, excluded from normal runtime. No assets, raw logs, saves or personal environment records published.
- Toolkit loose-file staging and separate English/Russian descriptions prepared. The owner selected the final artwork from HW Mod Previews. A512×512JPEG rendition (119402bytes) is attached to the local draft and launcher slot; source artwork remains outside Git. No Workshop create/update was called.

## Exact prepared and installed release

Fix revision: 82d260870455873f38bd047306959ef1c128c1fe6583d0dcc1900d920f27ea33 ·43overrides ·1128sourcefiles. Main BIG:105157948bytes. All7archives were fully extracted and compared to source; source/ownership/transport/capture/Dock/tooltip regressions passed. Installation/slot checks were completed after native smoke collection.

| Archive | SHA256 |
|---|---|
| HWMPPatch24.big | a9b9e2b4f6364e3dc770bd1f82ac5faeab9d95e12a622a6988b4e572fd585367 |
| English.big | 1d6bf714c4807f62759327d90ce7d619e1fa926c92062ee6a6459d79f6434b30 |
| French.big | 57b1b716aabcfe46ff0e4e32ea9bfa92791c6da8edea3887cbdba9587a9e1745 |
| German.big | ed37bc1a89e29838cf2f1d345b32239eb995bd57d3ca3f1d6c1064c44d589003 |
| Italian.big | 4c73ceafd13623fcd3d036abe7efdd2c3aff7731c240d29c341f633f01e6d609 |
| Spanish.big | d2b43a161ec7d3e69f5fcbd25587fa12338e23315749cf1e07d896f1ca51b777 |
| Russian.big | b2fa4c93301405337aacc706598a18cabb95908a4dcdf13c7b67cdeb9b815e23 |

## Native smoke after review

Diagnostic run 5b9cd6e3f5333b30b89e6073992f79246a6eceaaeb6995e9f8223655f7ee53a5 inherits normal gameplay files byte-for-byte; only the declared inactive auto-load UI registration differs. No Computer Use interaction was performed in these four successful runs.

| World | Result | Native journal SHA256 |
|---|---|---|
| JournalRecycle | 2 passed | 2ffd1a6bfa8fa1ea251718a7fcf1fc5ad45fe6668a2bfcd7c74db000faabf7bf |
| SaveLoadAuto | 2 passed | 175919c762108330792e02f1644a33fb7e1be3ac35767edca41c8dba9357936d |
| SaveLoadCold | 2 passed | 23cca1f833a1c49bc6f89552e7b132d9c617f69b7c76ed1d8793aa253c155fb6 |
| SaveLoadCoop | 2 passed | 97dbec79f9a1c585d97ab5d342cffbc706dca4e6ab25aebda275a0dffde8724c |

These cover recreation after all old anchors die, actual save/load/range exit and post-release movement, a new process, and preserving a scenario's allowed baseline. Earlier Empty/stress/transport/capture proofs remain identified in GRAVITY_SAVELOAD_FIX.md; they are not claimed as newly rerun. The review adds no new combat numbers or general FPS claim; prior individual pressure samples were about6–9% wall-time overhead versus control.

The window-capture-only pilot returned FrameArrived timeout and exited before valid results. It is excluded from all pass counts. The initial stdin probe timed out because WorkshopTool is a Windows GUI application. Its live command-field help was then successfully exercised through accessibility, confirming create/update syntax and controllable input; the tool was closed normally. Actual upload was deliberately not attempted. Steam authorization/agreement may still require the owner. The staged content, description and owner-selected preview are ready for review before an approved upload.

## Remaining

The [field checklist](CLOSURE_CHECKLIST.md): real two-client MP, ordinary/2x starts and languages, visible repair/replenishment, paid UI hyperspace/cancel/Guard and full matches. New-race single-player holding is allowed to be reconsidered by the author; its design/integration is not implemented here. Consumer pins/builds unchanged. Workshop is unlisted/unpublished, awaiting explicit publication approval after description/preview review.
