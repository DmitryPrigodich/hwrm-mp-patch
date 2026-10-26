"""Single release inventory shared by packaging, installation and publication staging."""

from language_data import LANGUAGES

RELEASE_DOCS = (
    "NATIVE_TESTS.md",
    "AUTO_TESTS.md",
    "AUTO_TEST_RESULTS.md",
    "NATIVE_FOLLOWUP_2026-10-25.md",
    "CLOSURE_CHECKLIST.md",
    "GRAVITY_SAVELOAD_FIX.md",
    "UPDATE_WORKFLOW.md",
    "PATCH_ENGINEERING.md",
    "LOCAL_INSTALLATION.md",
    "LOCALIZATION.md",
    "WORKSHOP.md",
    "MENU_BRANDING.md",
)
RELEASE_RUSSIAN_DOCS = (
    "UPDATE_WORKFLOW.md",
    "PATCH_ENGINEERING.md",
    "LOCAL_INSTALLATION.md",
    "LOCALIZATION.md",
    "WORKSHOP.md",
    "MENU_BRANDING.md",
    "CLOSURE_CHECKLIST.md",
)

RELEASE_PAYLOAD = frozenset(
    {
        "HWMPPatch24.big",
        *(language + ".big" for language in LANGUAGES),
        "config.txt",
        "README.md",
        "README.ru.md",
        "version.json",
        "HWMP Patch 2.4.cmd",
        "start_hwmp_patch.ps1",
        *RELEASE_DOCS,
        *(name.replace(".md", ".ru.md") for name in RELEASE_RUSSIAN_DOCS),
    }
)
