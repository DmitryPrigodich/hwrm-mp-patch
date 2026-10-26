# Main menu identity and music

[Русский](ru/MENU_BRANDING.md)

The26October front-end update uses existing native assets: the blue planetary HW2campaign backdrop, the stock Homeworld/Remastered wordmark and the white Taiidan badge. It adds the literal product subtitle **Multiplayer Patch2.4** using the game's Heading2Font. These English brand strings are intentional in every language; other menu buttons remain natively localized.

The original wordmark is displayed with UVs cropped to rows0–192of its1024×512source, excluding the baked Hiigaran symbol. The Taiidan emblem is an independent square graphic. Explicit numbered child fields preserve Lua4 table syntax. The old engine version/build labels retain their names for native callbacks but are hidden/ignored; the remaining footer reads only **HWMP2.4**.

Menu music is the requested **Inhibitors**, native `data:sound/music/staging/STAGING_04`, also referenced by HW2RM mission4. Its WAV entry is present in shared Music.big, so no new audio or campaign music archive is packaged. Only FEMusic changes; FEBattleMusic, volume and tuning values stay native. As documented by the native sound config, FEMusic is also the fallback for missions without a selected track. No looping script or gameplay music callback is added.

`tools/menu_branding.py` generates the text overrides and copies three byte-identical native textures from the local cache. `baseline/menu-inputs.json` pins all sources and the shared music metadata. Textures are ignored/generated locally; they are not published in Git. Rebuild through hwmp24.py; do not hand-edit only the generated files. This is front-end presentation and does not alter ship/research/economy coefficients or consumer pins.

Checks: Lua4 parsing and Lua-table inspection confirm the hierarchy, exact footer and hidden native labels; the stock audio config differs only at FEMusic. Full source regressions and every primary/language archive are checked by the normal release workflow. Visual layout, native font size, hearing the selected song and returning from a match still need human confirmation in the real menu. No native launch is inferred from source checks.
