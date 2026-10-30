# Automatic diagnostic harnesses

[Русский](ru/AUTO_TESTS.md)

Diagnostics are separate Extra Missions packages. They are never normal runtime content. Preparation, syntax/CRC checks and a completion marker each prove only their stated scope.

General mechanics: tools/auto_testgrounds.py and tools/run_auto_queue.py. SU tests: [boundary guide](SU_BOUNDARY_TESTS.md), tools/su_boundary_tests.py and tools/su_accounting_tests.py. Tools/analyze_*.py parse local observations; human UI behavior and MP remain separate.

Before any native run obtain the human's test request. Preserve exact source/archive hashes and previous logs. Refuse an existing game; do not rebuild/install during a future-launch queue. Close only an identified owned process after a fresh endpoint/error. A healthy timeout remains open. No user game may be stopped.

Freshness is checked against the preceding log content and launch time, in addition to world/token selection. IsBuilding can mean a waiting queue: paid RU/completion are separate observations. Cross-producer progress remains unverified without independent proof; two queue flags are not a passing concurrency control.

[Current outcomes](AUTO_TEST_RESULTS.md), [manual checks](NATIVE_TESTS.md), [historical methods](archive/README.md).
