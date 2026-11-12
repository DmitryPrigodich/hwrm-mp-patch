"""Copy the canonical effect/journal template and patch the pinned native gravity hook."""

from tool_safety import ensure_normal_python

ensure_normal_python()
from pathlib import Path


def generate_effects():
    return (Path(__file__).resolve().parent / "templates/effects.lua").read_text(encoding="ascii")


def patch_gravity(text):
    old = 'previously_stunned = SobGroup_CreateAndClear("gravwell-" .. ship_id .. "-previously-stunned")'
    assert text.count(old) == 1
    text = text.replace(old, "previously_stunned = HWJ_PreviousGroup(ship_id)")
    old = "else HWMP_BlockGroup(group, owner, GW_MEM_PROTO.abilities_to_disable, 1) end"
    assert text.count(old) == 1
    return text.replace(
        old,
        "elseif HWJ_OwnerHas(owner,group)==1 then\n            for i=1,getn(GW_MEM_PROTO.abilities_to_disable) do SobGroup_AbilityActivate(group,GW_MEM_PROTO.abilities_to_disable[i],0) end\n            SobGroup_SetSpeed(group,0)\n        else HWMP_BlockGroup(group, owner, GW_MEM_PROTO.abilities_to_disable, 1) end",
    )
