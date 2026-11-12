"""Always-on tool invariants. Optimized Python must fail before any side effect."""

import sys


def ensure_normal_python():
    if sys.flags.optimize or not __debug__:
        raise RuntimeError("HWMP tools require Python assertions: remove -O/-OO and PYTHONOPTIMIZE")


ensure_normal_python()


def require(condition, message="Required tool invariant failed"):
    if not condition:
        raise RuntimeError(message)
