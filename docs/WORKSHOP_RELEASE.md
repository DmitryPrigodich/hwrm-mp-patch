# Workshop publication — 12 November 2026

[Русский](ru/WORKSHOP_RELEASE.md)

[HWMP Patch 2.4.6](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) updates the existing item **3827773780**. Public Steam metadata confirms the title, visibility, owner-supplied original cover and description explaining SU removal in English and Russian. Manifest: **5924341424333373576**. The Toolkit removed blank lines only; the actual public text is mirrored in workshop/description.en.bbcode. [Release receipt](../workshop/published-release.json), [previous 2.4.5](../workshop/releases/2.4.5-before-2.4.6.json).

## Released behavior

Support Units, the Cataclysm mode, its HUD and SU prices are removed. Classic unit caps are restored. Shared fixes, six-collector starts, approved Assault coefficient 1.2, six-language tooltips, Russian naming corrections, emblems and music remain. Source commit `b0e3f9f632e949e8cfcd5ff086888215159a64e1`; fix `f6941b453b836532f7ec7ba15a444199c1722a9e2203c72342d6e3de092c0ef4`; developer primary `2c28e330b30ecd834a6fcf415e1570bc86954721c7543397c7d94aeb03c17409`. Code and documentation were pushed without game assets.

## Verification and remaining work

Passed: 13 asset-free tests, Black/Pyflakes, source/regression checks, 170 Lua 4 parses, all 113 ordinary ship definitions and 62 classic cap comparisons, full developer seven-BIG extraction comparison and ZIP/checksum checks. The exact developer package was installed with a verified previous-package backup; Russian native launch loaded both expected archives without detected fatal errors. The owner reported that the build looks good and confirmed checking it. No individual full-match or two-client acceptance is inferred.

**Actual Steam download verification is pending.** At the last check, the local subscription retained the previous manifest. Its prior files are backed up locally. The seven downloaded Steam BIGs have not yet been compared with the 1140 staged resources; developer archive checks and public metadata do not replace that check. No native launch of a downloaded 2.4.6 Workshop package is claimed.

Existing item ID, other mods, original BananaDLC and downstream repositories remain unchanged. [Known issues](KNOWN_ISSUES.md), [field acceptance](CLOSURE_CHECKLIST.md).
