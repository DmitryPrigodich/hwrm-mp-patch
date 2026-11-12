# Current handoff — 12 November 2026

## Published 2.4.6

Owner requested removing SU, keeping other code/documentation improvements, building, testing and publication with the original attached cover. Workshop item 3827773780 is now public as HWMP Patch 2.4.6, manifest 5924341424333373576. Public title, description content and exact cover hash were verified through Steam. The short SU explanation is in English and Russian; classic caps are restored. [Release report](docs/WORKSHOP_RELEASE.md), [receipt](workshop/published-release.json), [review](docs/REVIEW_2_4_6.md).

Source commit b0e3f9f632e949e8cfcd5ff086888215159a64e1 was pushed to codex/hwrm-mp-patch; the publication-documentation follow-up follows it. No assets, caches, raw logs or private profile data are tracked. The previous 2.4.5 receipt remains in workshop/releases/2.4.5-before-2.4.6.json. No downstream pin/build changed.

## Package and validation

Package: local/HWMPPatch246-candidate and its ZIP. Version 2.4.6, SU disabled. Main SHA256 2c28e330b30ecd834a6fcf415e1570bc86954721c7543397c7d94aeb03c17409; ZIP SHA256 b3e38bba7060289568125cca33d1fa0270f66ff53e072dd4fa82e74e13b01342; content aca324e8af1bf2e33c1e857ec4e72a84bea0c94f6efa3927d5c0f71c70f46bdb; fix f6941b453b836532f7ec7ba15a444199c1722a9e2203c72342d6e3de092c0ef4. Post-publication prose was refreshed without changing any BIG. Previous package/ZIP are preserved in local/workshop-246-20261112/pre-publication-release and its ZIP.

Passed: 13 asset-free tests, Black/Pyflakes, source/mechanic/localization checks, 170 Lua 4 parses, all 113 ordinary ship definitions and 62 classic caps, full developer seven-BIG comparison and ZIP checks. Canonical effects preserve former Lua bytes; frozen examples remain unchanged. All earlier SU proposals and Test1 remain isolated references.

Installed via the owned installer after the owner closed the launcher, with verified backup local/installed-backups/20261112T002516561091Z/HWMPPatch24. Protected packages and other mods were unchanged. Russian native launch loaded both expected archives without detected fatal errors. Window capture timed out twice; the owner subsequently said the build looks good and confirmed checking it. Do not infer full-match or two-client acceptance from that report. Native evidence: local/native-tests/20261112T002506167929Z/. Never stop the user's running game.

## Remaining check

The actual subscribed Steam download still retained the former manifest at the last check. Previous subscription files were backed up to local/workshop-246-20261112/previous-steam-download. The downloaded seven-BIG CRC/full extraction comparison remains pending; metadata success and developer-package checks do not replace it. Local publication scripts/evidence: local/workshop-246-20261112; helper scripts remain in the campaign workspace's ignored local/publish246. Steam UI capture is unreliable; no subscription deletion, client restart or other-mod mutation was performed. Future checks must use a fresh manifest and must not stop a human game.

The normal local developer slot is 2.4.6. The separate launcher Banana slot and campaign package were not replaced. Recommend Medium for routine follow-up, High for renewed engine accounting/release diagnosis; app setting unchanged.
