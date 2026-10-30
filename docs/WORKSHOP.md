# Workshop update procedure

[Русский](ru/WORKSHOP.md)

Existing item: [3827773780](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780). Retain its ID and the owner-selected cover; later authorized releases use update, never create a duplicate.

1. Review code, current EN/RU descriptions and known limitations. Run source/fixtures/Lua4 and fully extract/compare all seven candidate archives. Commit/push code/docs without assets.
2. Stage loose runtime using tools/prepare_workshop.py --candidate --preview <approved512image> --title <title>. The Toolkit consumes loose files, not prebuilt BIGs. No diagnostic worlds, source tools or private logs belong in the payload.
3. Publish only within the user's explicit authorization. Preparation alone is not publication permission. The current user request authorizes this update with the revised description of SU defects; show the concrete final text before submission. Keep title/description within128/8000characters, image512×512 below1MiB, GameType HomeworldRM, ModType MOD and the existing WorkshopID.
4. Use the installed Toolkit's documented update command with the staged folder. Do not handle authentication codes/passwords or accept author obligations for the owner.
5. Verify public title/description/cover and manifest. Download the actual subscribed package, CRC-test and fully extract/hash-compare all seven BIGs against staged loose source. Toolkit and developer archive hashes may differ.
6. Preserve the previous receipt under workshop/releases; update workshop/published-release.json, the current release report and Git. Source composition/download comparison is not a native game/two-client test.

Current limitations: [known issues](KNOWN_ISSUES.md). Current publication: [report](WORKSHOP_RELEASE.md). Prior uploads/primary local references: [archive](archive/README.md). No downstream pin/build or local game installation is implicit in publication.
