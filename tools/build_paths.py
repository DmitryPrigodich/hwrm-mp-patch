"""Explicit, isolated paths for each build variant; no mutable release selection."""

from tool_safety import ensure_normal_python

ensure_normal_python()
from dataclasses import dataclass
from pathlib import Path
from hwrm_common import PROJECT, build_directory
from project_version import VERSION


@dataclass(frozen=True)
class BuildPaths:
    work: Path
    build: Path
    release: Path

    @property
    def source(self):
        return self.build / "source"


def paths(candidate=False):
    kind = "candidate" if candidate else "release"
    version = VERSION.replace(".", "")
    return BuildPaths(
        PROJECT / "local/builds" / VERSION / kind,
        build_directory("hwmp-" + VERSION + "-" + kind, PROJECT),
        PROJECT / "local" / ("HWMPPatch" + version + "-" + kind),
    )
