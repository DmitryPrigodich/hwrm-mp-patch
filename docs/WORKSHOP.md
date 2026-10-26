# Workshop preparation and publication gate

[Русский](ru/WORKSHOP.md)


Current item **3827773780** is public and verified against the Steam download. [Release report](WORKSHOP_RELEASE_2026-10-26.md). Staging preserves the ID from workshop/item.json; later uploads use update when authorized.

The installed **Homeworld Remastered Toolkit** includes WorkshopTool.exe, Archive.exe, ReadMe.txt and a commented config.txt. Its ReadMe/config are the primary local references; the [developer's upload guide](https://steamcommunity.com/sharedfiles/filedetails/?id=398897438) describes the same loose-file workflow.

## What must be prepared

- A folder of **loose runtime files**, not the already-built BIG. The supplied tool packs the data and sibling language BIGs itself.
- config.txt: Title up to128characters, GameType:HomeworldRM, ModType:MOD, a space-free BigFilename, space-separated Tags, WorkshopID:0 for a new item and Description up to8000characters.
- preview.jpg or preview.png, exactly512×512 for this Toolkit, below1MiB. A larger landscape promotional image can be kept separately for the page.
- English description as the source; Russian description in a separate file. Native language directories remain distinct. Retain upstream credits and state that this is a field-test candidate.

`python tools/prepare_workshop.py --preview <approved512image>` produces ignored local/Workshop-upload. Omit --preview to stage content before artwork is ready; later use `python tools/attach_workshop_preview.py <owner-selected-square-image>` for a composition-preserving512×512JPEG rendition. It verifies normal source/release identity and copies only runtime files plus approved publication metadata. No examples, source utilities, private logs, saves, credentials or local settings are included.

## What the assistant can do

Prepare/verify files, inspect the installed tool/help, stage a native screenshot scene, create clearly labeled illustrative artwork if capture is unavailable, show drafts, and later run an approved Toolkit create/update command using the existing Steam session. It cannot enter passwords/Steam Guard codes or accept author/legal obligations on the user's behalf. If Steam authorization or an agreement is required, the owner handles that step.

**Preparation is not publication approval.** The first upload was authorized and completed on 26 October 2026; preparation alone does not authorize a later create/update. Show description/preview first and wait for the owner's decision. Do not silently publish a private placeholder either. After first publication preserve the WorkshopID written by the tool; do not use0for an update or overwrite another author's item.

Once approved, launch the installed Toolkit in its documented working directory and use `create <absolute staged folder>` for the first item or `update <folder>` for its assigned ID. Live command-field help/input has been verified in the installed GUI; actual upload is intentionally unattempted until approved. The owner may need to confirm the Workshop agreement in Steam.

After upload, subscribe to the actual item and check it through **Mods → Remastered**. Record downloaded artifact hashes, menus/languages and a native start. Toolkit repacking may produce different binary hashes from our local verified BIG; validate the uploaded payload rather than assuming equivalence.

Original game assets are excluded from Git but are needed locally to build this full patch. Credit is preserved; this does not represent a legal ownership audit of third-party contributions. Review inherited permissions/attribution before final publication.
