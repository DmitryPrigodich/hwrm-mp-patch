"""Render canonical repository docs into the release's flat EN/RU layout."""

from pathlib import Path
import re
from hwrm_common import PROJECT
from release_layout import RELEASE_DOCS, RELEASE_RUSSIAN_DOCS

CODE_URL = "https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/"


def document_map():
    return {
        PROJECT / "README.md": "README.md",
        PROJECT / "README.ru.md": "README.ru.md",
        **{PROJECT / "docs" / name: name for name in RELEASE_DOCS},
        **{
            PROJECT / "docs/ru" / name: name.replace(".md", ".ru.md")
            for name in RELEASE_RUSSIAN_DOCS
        },
    }


def write_release_docs(release):
    documents = {source.resolve(): name for source, name in document_map().items()}
    for source, name in documents.items():

        def link(match):
            target = match[1]
            if re.match(r"[A-Za-z]+:|#", target):
                return match[0]
            file, separator, fragment = target.partition("#")
            resolved = (source.parent / file).resolve()
            if not resolved.is_relative_to(PROJECT):
                raise ValueError("Documentation target escapes project: " + target)
            if not resolved.exists():
                raise ValueError("Missing documentation target: " + str(resolved))
            destination = documents.get(resolved)
            if destination is None:
                destination = CODE_URL + resolved.relative_to(PROJECT).as_posix()
            return "](" + destination + (separator + fragment if separator else "") + ")"

        text = re.sub(r"\]\(([^)]+)\)", link, source.read_text(encoding="utf8"))
        (Path(release) / name).write_text(text, encoding="utf8", newline="\n")
