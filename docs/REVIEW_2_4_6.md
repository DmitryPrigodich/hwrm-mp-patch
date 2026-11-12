# Review follow-through — 2.4.6 candidate

[Русский](ru/REVIEW_2_4_6.md)

Owner decision, 2 November 2026: remove SU if unreliable and preserve the independent improvements. Published 2.4.5 is unchanged; the candidate excludes SU entirely. Test1 remains an isolated, unpublished experiment, not a release feature.

Implemented: early refusal of optimized Python for every active tool; explicit critical pin/path checks; separate build paths and generated output per variant; portable package verification receipts; fresh staging with previous-package preservation and rollback; installer/native-test/Workshop preparation use explicit release paths; archive state restored on exceptions; asset-free CI/regressions; clearer current EN/RU documentation. Generated output lives in ignored per-build folders, while hand-maintained overrides are explicitly listed. Frozen examples remain unchanged.

Source tests check the full configurations of all 113 original ship types, original class caps, absence of SU mode/HUD/prices and retained mechanics/localization. Packaging fully extracts all seven BIGs. CI is prepared locally, not yet run on GitHub. This is not native game acceptance.

The gravity effect/journal template is consolidated without changing its generated Lua bytes. Performance tuning is deferred until comparative native measurements; no new timing claim is made. Historical SU tests and price proposals remain reference material.
