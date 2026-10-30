# SU budget rounding — 30 October 2026

[Русский](ru/SU_BUDGET_ROUNDING_2026-10-30.md)

The owner requested budgets divisible by32. The owner selected Normal1920, Large2560 and Vast7680; Small1440 and Huge3840 retain the initial rounding. Scale32, all113 ship prices and classic carrier/shipyard/probe caps remain unchanged.

| Profile | Previous SU | Prepared SU | Change | Percent | Native ceiling |
|---|---:|---:|---:|---:|---:|
| Small | 1450 | 1440 | -10 | -0.69% | 45 |
| Normal | 1900 | 1920 | +20 | +1.05% | 60 |
| Large | 2600 | 2560 | -40 | -1.54% | 80 |
| Huge | 3850 | 3840 | -10 | -0.26% | 120 |
| Vast | 7650 | 7680 | +30 | +0.39% | 240 |

Source of truth: design/cataclysm.json. Generator validation rejects fractional native ceilings or limits at/above250. The HUD denominator and all five native rule profiles come from the same data; its hidden initial placeholder is0/? rather than a duplicated Normal budget. Existing HUD fixtures cover all profiles. Historical accounting diagnostics keep their immutable1900-based source budgets and reject incompatible prices; the previous reports and evidence are unchanged.

This rounds ceilings only. [The known fractional-cost enforcement defect](SU_ACCOUNTING_2026-10-30.md) remains; this is not an accepted exact-SU fix or a stability improvement claim. Candidate preparation is separate from installation and publication. Installed HWMP/launcher slot, Steam and downstream pins remain unchanged; no new native launch is claimed.

Validation:113ship types/both modes,214Lua4 parses,360exact padding plans, effect/install fixtures and full7BIG comparisons passed. Prepared primary SHA256: `0fb9431e5acba646586ea8e3e880c599fe3243c6c0c177661da3299c6c982f3d`. No native test, installation or publication.
