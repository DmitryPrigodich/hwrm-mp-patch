# Workshop release — 26 October 2026

[Русский](ru/WORKSHOP_RELEASE_2026-10-26.md)

[HWMP Patch 2.4 - Field Test](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) is public, item **3827773780**, consumer app **244160**. The owner explicitly authorized the first upload. Toolkit app 347380 returned the item ID; the Steam client log confirmed successful content/preview upload. The unauthenticated Steam API returns result 1 and visibility 0 (public); the page was also checked in the owner's authenticated browser. The separate anonymous Community HTTP probe was rate-limited (429), so it is not recorded as a successful page check. The selected cover, field-test status and all contributor names were checked. The owner's live description formatting was copied back into the English source; it was not overwritten.

Source commit: `139f361e8f61d74ca2f6fa3ad9f3a657df737cd7`; fix: `b9ef33908806ad049bb135ba72220e94454db870aed16ed6a00cfba24850e846`. Steam content manifest: **2584013199517664159**. Public identity/hashes: [item](../workshop/item.json), [release receipt](../workshop/published-release.json).

The actual Steam subscription download was verified: seven BIGs passed CRC and full extraction/hash comparison against all **1136** prepared runtime files. Primary BIG contains 1130 data files; each of six language BIGs contains one locale Lua resource. TOC aliases are native data/locale. The downloaded preview matches the selected source SHA256. Total downloaded files: **110014186 bytes**.

Toolkit repacked the archives: Steam primary SHA256 **6733149b5ec78f9cefeaf3dce771e2d1e968bb6fabc49b8bced866ced94523ab**, local development primary **0e306ebe298f9bd183d5eeca3b9aa783017c7cd096e63013a9000b4c6e9ccb82**. The local archive also contains an English fallback TOC; Workshop supplies the native sibling English.big. Full extraction proves the intended resources, not native engine/multiplayer compatibility between differently packed releases. Use matching Workshop copies on all peers. This publication did not launch the game; menu/native language loading and two-client/full-match acceptance remain human tests.

Future staging reads workshop/item.json and retains **3827773780**. Use WorkshopTool **update**, not create; keep the assigned ID and obtain authorization for a subsequent upload. Source preparation alone never publishes. No consumer dependency pins or builds advanced. The reversible local launcher slot and its previous VR backup were retained.
