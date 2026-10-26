# Localization

[Русский](ru/LOCALIZATION.md)

English is the primary README/documentation and direct-starter language. Russian has README.ru.md and separate docs/ru files. Runtime language remains selectable; the developer's local Steam language is not imposed on other users.

## Supported native languages

| Game folder/API locale | Language | New labels |
|---|---|---|
| English | English | Base time / Value / s |
| French | Français | Durée de base / Valeur / s |
| German | Deutsch | Basisdauer / Wert / s |
| Italian | Italiano | Tempo base / Valore / s |
| Spanish | Español (Spain) | Tiempo base / Valor / s |
| Russian | Русский | Базовое время / Значение / с |

These six are present as native language BIGs and in the installed launcher's language selection. This is not a claim to support every language listed by Steam generally. No new playable entity is introduced by this patch: original game names and descriptions use existing IDs. The internal ScoutSpeedLimiter identifier is not a player-facing name.

## Source and fallback policy

`localization/hwmp24.json` owns the three added tooltip labels for each language. Build/research descriptions come from native `.ucs` or textual `.dat` files, pinned by native archive SHA in baseline/native-locale-inputs.json. English retains the pinned upstream helper's text. A missing native entry explicitly falls back to its English text; missing/empty descriptions are not replaced with invented ship text.

`language_data.py` reports exact fallback IDs and coverage in ignored local/localization-coverage.json; the publication review records a sanitized summary. The generated locale/*/hwmp24_tooltips.lua files contain ASCII decimal escapes for UTF8 bytes, preserving Lua4 compatibility. Translation completeness is not a native visual/font check: the four additional-language labels are drafts pending speakers' review.

New strings must have an English source, all supported-language values and a short context. Do not duplicate Russian into English or translate technical IDs. Preserve stock UI localization; do not rewrite inherited balance descriptions wholesale. If a new playable entity is later introduced, give its name/description explicit dictionary IDs and record gaps before publication.

## Packaging and checks

The main BIG contains data plus English fallback. Each of the six sibling `<Language>.big` files uses the native alias `locale`. Never use aliases such as `locale:Russian`: that syntax is not supported by native archive loading. Each archive is fully extracted and compared to its source.

The tooltip checks run the actual four race build tables through each dictionary, verify seconds/base-time/value labels and preserve unknown/nil/empty descriptions. French accents, German text, Cyrillic, wrapping and ordinary menu selection still need field review. Diagnostic Extra Missions are developer tools with English/Russian captions; additional-language diagnostic captions may use English fallback and are not part of the normal mod.

Useful sources: the installed Toolkit WorkshopTool/ReadMe.txt and config.txt; [Steam's HWRM page](https://store.steampowered.com/app/244160/Homeworld_Remastered_Collection/). Preparation and scripts use your installed native archives, not web translations of stock ship names.
