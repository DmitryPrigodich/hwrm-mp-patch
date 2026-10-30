"""Check current Markdown links, EN/RU release pairs and source/readme consistency."""

from pathlib import Path
import re
from hwrm_common import PROJECT
from release_docs import document_map, write_release_docs
import tempfile


def broken_links(path, root):
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf8"), flags=re.S)
    problems = []
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if re.match(r"[A-Za-z]+:|#", target):
            continue
        file = target.partition("#")[0]
        resolved = (path.parent / file).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
            problems.append((str(path.relative_to(root)), target))
    return problems


def verify():
    current = [
        PROJECT / "README.md",
        PROJECT / "README.ru.md",
        *(PROJECT / "docs").glob("*.md"),
        *(PROJECT / "docs/ru").glob("*.md"),
    ]
    errors = [error for p in current for error in broken_links(p, PROJECT)]
    assert not errors, errors
    documents = document_map()
    assert all(p.exists() for p in documents), [str(p) for p in documents if not p.exists()]
    with tempfile.TemporaryDirectory(prefix="release-docs-", dir=PROJECT / "local") as folder:
        write_release_docs(folder)
        paths = list(Path(folder).glob("*.md"))
        errors = [error for p in paths for error in broken_links(p, Path(folder))]
        assert not errors, errors
        assert len(paths) == len(documents)
    return dict(
        status="passed",
        current_markdown=len(current),
        release_documents=len(documents),
        current_and_flat_release_links_checked=True,
    )


if __name__ == "__main__":
    import json

    print(json.dumps(verify()))
