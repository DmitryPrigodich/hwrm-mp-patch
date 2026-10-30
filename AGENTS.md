# hwrm-mp-patch

English is primary; Russian current docs live in docs/ru. Read NEXT_SESSION.md, docs/README.md, docs/UPDATE_WORKFLOW.md, docs/PATCH_ENGINEERING.md and docs/CLOSURE_CHECKLIST.md before changes. Project chronology is under docs/archive, not current policy.

- This base owns shared fixes and the original four races on pinned Players Patch2.3Test build21. Dependency direction: base→HW1 race layer→campaign. Never auto-build/install or advance consumer pins.
- Authoritative runtime: generators/templates and design/cataclysm.json. Regenerate outputs; check both ordinary/Cataclysm branches, Lua4 parsing, effect/install fixtures and full payload extraction of all seven BIGs. Mocks/CRC/composition are not native engine validation.
- Approved balance:6/6 collectors, Assault final535/1.2, two scoped missile corrections; Cataclysm budgets1440/1920/2560/3840/7680. Ship SU prices and count caps are unchanged. Carriers add no capacity.
- Cataclysm native weighted enforcement is KNOWN DEFECTIVE: early refusal and guarded paid overflow reproduced. Integral ceilings do not repair fractional ship prices. HUD counts nominal owned entries, not queues or physical surviving hulls. See docs/KNOWN_ISSUES.md.
- Keep original permissions/speed and overlapping ownership in the native journal. Old active-well saves lacking metadata are not guaranteed. Do not globally unfreeze targets. Campaign transitions/transport saves and two-client synchronization need their own tests.
- Do not invent native API availability from strings or mocks. Lua4 differs from Lua5; native data/locale aliases are required. Keep all six native localization overlays and upstream credits.
- Native game/launcher tests/install need the human request. Never stop the user's game. A runner may close only its identified owned process after a fresh endpoint/error; healthy timeouts remain open. Never rebuild/install under an active future-launch queue.
- Install only through the owned installer with exact path validation, preserved prior packages and closed processes. Preserve original BananaDLC, other mods and the backed-up Vast Reaches launcher slot. No game/launcher auto-start from preparation.
- Workshop3827773780 is the existing update target; retain its ID and owner-selected cover. Publish only within the user's explicit authorized scope, after concrete reviewable preparation. Verify actual Steam payload; developer/Toolkit hashes can differ. Never upload raw logs, process/profile data or assets to Git.
- Git is code/docs/localization/pinned metadata only. No models/media/BIGs/cache/backups/saves/credentials. examples/native-testgrounds is frozen reference; never import it into normal runtime or silently rewrite its manifest.
- Keep current behavior/known issues in Markdown near the documentation entry points; historical/rejected experiments in docs/archive. JSON is functional input, pins or machine receipts, not a prose history. Preserve literal upstream and original source-language records.
- Recommend High for native compatibility/accounting diagnosis and substantial review; Medium for routine follow-through. Recommendations do not change app settings.
