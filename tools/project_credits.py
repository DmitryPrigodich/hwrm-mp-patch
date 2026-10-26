"""Shared attribution for menus, launcher metadata and publication descriptions."""

HWMP_CONTRIBUTORS = ("AmDDRed", "Hix", "Twofoxich")
PLAYERS_PATCH_CREDITS = {
    "Gameplay options and features": (
        "Cloaked",
        "NoOne",
        "QuadS",
        "Sastrei",
        "Lif",
        "Dwarfinator",
    ),
    "Bug fixes and improvements": (
        "Trebic",
        "Cloaked",
        "NoOne",
        "Fear",
        "QuadS",
        "Echo",
        "Stuart",
        "Gunnerth",
        "radar",
        "Lone Wolf",
        "Dom2",
        "HW_Lover",
        "178thBattleGroup",
        "CryCoh",
    ),
    "Campaign improvements": ("NoOne", "Echo", "Cloaked", "Stuart"),
    "Balance": ("Cloaked", "Fear", "Kadeshi", "QuadS", "omniconsumer"),
}
WORKSHOP_CREATORS = {
    "Players Patch 2.3": (
        "omniconsumer",
        "Trebic",
        "Gunner",
        "Cloaked",
        "Kadeshi",
        "| Stuart98 ||",
        "Echo",
        "CPU8",
        "Fear",
        "NoOne",
    ),
    "2.3Test": ("Cloaked", "Echo", "CPU8", "Fear"),
}
from project_version import VERSION

SHORT_CREDITS = (
    f"Credits: Players Patch 2.3 team; 2.3Test: Fear/Novaras; HWMP {VERSION}: "
    + ", ".join(HWMP_CONTRIBUTORS)
    + "."
)
# Proper names and project titles stay unchanged in all native languages.
MENU_CREDITS = SHORT_CREDITS.replace("; ", " | ").removesuffix(".")
