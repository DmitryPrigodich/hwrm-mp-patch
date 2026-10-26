"""Explicit stock-identical asset omissions and missile model aliases.

No donor or native file is edited. Fail closed on changed input hashes.
Source equality is not proof that a native model-loading call works.
"""

import hashlib
import json

from hwrm_common import CACHE, DONOR, GAME, PROJECT, donor_runtime, index, sha

POLICY = PROJECT / "baseline/stock-asset-fallbacks.json"
LOAD_HOD = "LoadHODFile(NewShipType,1);"


def policy():
    result = json.loads(POLICY.read_text(encoding="utf8"))
    assert result["schema"] == 1
    return result


def content_revision(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def shared_definition(row, text):
    """Change only the model binding, retaining all type/behavior coefficients."""
    assert row["method"] == "shared_model"
    assert text.count(LOAD_HOD) == 1, row["definition"]
    return text.replace(LOAD_HOD, 'LoadSharedModel(NewShipType,"' + row["model"] + '");')


def validate_inputs():
    data = policy()
    for name, archive in data["archives"].items():
        assert sha(GAME / "HomeworldRM/Data" / name) == archive["sha256"], name
    seen = set()
    for row in data["assets"]:
        name = row["path"]
        assert name not in seen and donor_runtime(name), name
        seen.add(name)
        assert sha(DONOR / name) == row["sha256"], name
        archive = data["archives"][row["archive"]]
        native = CACHE / "players-patch-audit" / archive["folder"] / row["stock_path"]
        assert sha(native) == row["sha256"], str(native)
        if row["method"] == "same_path":
            assert name == row["stock_path"]
        else:
            assert row["method"] == "shared_model"
            assert row["stock_path"] == f'missile/{row["model"]}/{row["model"]}.hod'
            shared_definition(row, (DONOR / row["definition"]).read_text(encoding="ascii"))
            # LoadSharedModel also redirects events. Reject merely identical geometry.
            donor_events = (DONOR / name.replace(".hod", ".events")).read_text(encoding="ascii")
            stock_events = native.with_suffix(".events").read_text(encoding="ascii")
            assert donor_events == stock_events, "Would replace distinct missile effects: " + name
            assert (
                hashlib.sha256(donor_events.encode("ascii")).hexdigest()
                == row["events_text_sha256"]
            )
    return data


def generate_aliases(destination, data):
    for row in data["assets"]:
        if row["method"] != "shared_model":
            continue
        source = (DONOR / row["definition"]).read_text(encoding="ascii")
        path = destination / row["definition"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(shared_definition(row, source), encoding="ascii", newline="\n")


def verify_composition(source, manifest, upstream, overrides):
    data = validate_inputs()
    assert manifest["stock_asset_fallbacks"] == data
    omitted = {row["path"] for row in data["assets"]}
    inherited = {name for name in upstream if donor_runtime(name)} - omitted
    assert set(manifest["base_runtime_files"]) == inherited
    files = index(source)
    assert set(files) == inherited | set(overrides) | {"hwmp24-id.txt"}
    assert not omitted.intersection(files)
    assert manifest["content_revision"] == content_revision(manifest["files"])
    aliases = set()
    for row in data["assets"]:
        if row["method"] == "shared_model":
            name = row["definition"]
            expected = shared_definition(row, upstream[name].read_text(encoding="ascii"))
            assert files[name].read_text(encoding="ascii") == expected, name
            assert name in overrides
            aliases.add(name)
    return aliases
