# Main menu identity and music

[Русский](ru/MENU_BRANDING.md)

The front end uses the native HW2 planetary backdrop and Homeworld/Remastered wordmark. Below the wordmark, three separate white badges appear in order: **Hiigaran, Vaygr, Taiidan**. The literal subtitle **Multiplayer Patch 2.4** sits below that row in Heading2Font. Product names stay English in every language; menu buttons retain their native localization. The footer reads **HWMP 2.4**.

The wordmark shares a 1024×512 atlas with a blue Hiigaran emblem. Its upper 192 rows contain the complete wordmark and underline; the emblem begins at row 209. The corrected `uvRect = {0, 0.375, 1, 0}` selects those upper rows. The first attempt selected the bottom 192 rows and displayed an emblem fragment instead of the title, as confirmed by the owner's screenshot. Each badge now uses a separate native texture, equal square bounds and a shared vertical center. Explicit numbered child fields preserve Lua 4 syntax.

The original engine version/build labels retain their names for native callbacks but are hidden. The separate patch label supplies the clean footer without changing the engine's network version.


The Game Type list now reads `Homeworld RM - HWMP 2.4`, `Homeworld 1 RM - HWMP 2.4` and `Homeworld 2 RM - HWMP 2.4`. These are literal product names in every language. Only GameRulesName changes in each pinned rule script; GUID, SaveGameVersion, race/map filters, options and gameplay code are preserved.

Menu music is **Inhibitors**, native `data:sound/music/staging/STAGING_04`, also referenced by HW2RM mission 4. Its WAV entry is present in shared Music.big, so no new audio or campaign music archive is packaged. Only FEMusic changes; FEBattleMusic, volume and tuning values stay native. The native config also uses FEMusic as a fallback for missions without a selected track. No looping script or gameplay music callback is added.

`tools/menu_branding.py` generates the text overrides and copies five byte-identical native textures from the local cache. `baseline/menu-inputs.json` pins the inputs and shared music metadata. Textures are ignored/generated locally and are excluded from Git. Rebuild through hwmp24.py; edit the authoritative template rather than only its generated copy. No ship, research, economy coefficient or consumer pin changes here.

Checks cover Lua 4 parsing, Lua-table inspection, the selected atlas rows, badge ordering, the footer and unchanged battle-music settings. Normal release verification extracts and compares every primary/language archive. The corrected layout, font rendering and music still need confirmation in the real menu; source and archive checks do not provide that confirmation.
