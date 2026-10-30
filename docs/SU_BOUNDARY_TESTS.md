# SU diagnostic scenarios

[Русский](ru/SU_BOUNDARY_TESTS.md)

These are isolated diagnostics, not ordinary mod content. [Current known defect](KNOWN_ISSUES.md); [archived native evidence](archive/2026-10-30/SU_ACCOUNTING_2026-10-30.md). Historical1900 results remain attached to their original source; they are not relabeled for1920.

## Boundary suite

tools/su_boundary_tests.py prepare generates52worlds:12manual cases plus one six-case Auto world per race. Current prices per interceptor entry: Hiigaran15, Vaygr14, Kushan3, Taiidan3. Every world pads the owned baseline exactly for all five configured profiles (360plans).

| Case | Initial free SU | Observe |
|---|---:|---|
| Control |200| Paid completion must work before interpreting a rejection |
| Under / Exact / Above | price−1 / price / price+1 | Queue, RU spent and actual completion separately |
| Full / Over |0 / −1| No further paid completion should be admitted |
| Parallel / ParallelExact |2×price−1 /2×price| Both producers' actual progress, not queue flags |
| Cancel / Pause |2×price−1| Released/retained reservation and resumed admission |
| ProducerLoss |2×price−1| Carrier loss frees40SU itself; separate it from canceled reserve |
| FleetLoss |price−1| Destroy the expendable collector; freed capacity should unblock production |

For current Hiigaran Normal 1920, Exact starts at1905. Close the preceding manual session before another launch. Two carriers are nearby; protected filler is far away. Commands: prepare, install, launch Hgn_Exact --language Russian, collect. Native install/launch needs the human's request.

Automatic boundary worlds deliberately call low-level Build even after a negative CanBuild; they probe a bypass and are NOT UI-admission proof. Queue flags do not count as paid progress. Cross-producer cases stay inconclusive without independent concurrent-production evidence.

## Accounting suite

tools/su_accounting_tests.py prepare --scale 32 or prepare --scale 64 copies an immutable prepared boundary source. Measure samples original-type counts; Equal compares equal nominal fleets; EqualBuild requires CanBuild=1 before EACH sequential paid request; QuantumLow/High use identical probe definitions with one test family each. Source budgets/prices are taken from the frozen source. Equal baselines follow its Normal budget−15 (1885 in the archived1900 source;1905 in a fresh1920 source). Smaller unsupported equal baselines fail explicitly. Equal worlds require the Normal profile.

Prepared worlds: Hgn_Measure, Hgn_Equal, Hgn_EqualBuild, Hgn_QuantumLow, Hgn_QuantumHigh, Hgn_Auto. Reprepare before install/launch after selecting a scale. This tool does not install or launch merely by preparing. Collect uses a launch-time/content freshness guard plus world/token filtering; close-terminal requires the owned fresh endpoint/error. A healthy timeout remains open.

Raw logs, source copies, rejected pilots and process metadata stay in ignored local/su-boundary-tests. No real game/two-client pass follows from Lua parsing or package comparison. [Automatic test policy](AUTO_TESTS.md).
