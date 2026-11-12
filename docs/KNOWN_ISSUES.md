# Known issues and validation

[Русский](ru/KNOWN_ISSUES.md)

## Version 2.4.6

Support Units is removed, not advertised as repaired. Classic unit caps are restored. The earlier Access Violation cause remains unknown; completed diagnostics without a crash do not certify full matches. Two-client synchronization, full-match balance, physical squadron replenishment and campaign transitions require their own native tests. Old active-gravity saves made before the checkpoint journal may lack original ability baselines. Specific new gravity save/load cases passed on their recorded older artifacts.

Source, Lua 4, regression and full developer archive checks passed. The exact developer package completed a basic Russian native launch, and the owner confirmed that it looks good. This does not establish full-match, two-client or downloaded Workshop-package acceptance. Report version/archive hashes, mode, race, actions and observed behavior. [Acceptance checklist](CLOSURE_CHECKLIST.md).

## Historical 2.4.5

Workshop now contains 2.4.6 without SU. The previous 2.4.5 SU limiter was defective. Of 99 positive-price ship types, 76 cost at most 16 SU. Their weights after division by 32 fall in the range that contributed zero in controlled native tests. For example, a 15-SU interceptor received weight 0.46875; a 20-SU marine frigate received 0.625 and contributed one native unit (32 nominal SU) in controlled tests. This is a serious composition-dependent mismatch; Layout and retained count caps still apply. These observations are not a universal precision contract for all engine APIs/types.

Ordinary UI refused 15 SU at 1885/1900. Guarded paid backend requests also completed to 1915/1900. Divisors 32/64 and rounded ceilings did not fix the mechanism. The unpublished Test1 periodic gate does not atomically reserve queues and may overflow or stall production. [Historical investigation](archive/2026-10-30/SU_ACCOUNTING_2026-10-30.md), [Test1](CATACLYSM_2_4_6_TEST.md).
