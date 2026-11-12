"""Asset-free regression suite. Run: python -m unittest discover -s tests -v."""

import ast
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


class SafetyTests(unittest.TestCase):
    def test_optimized_tools_refuse_before_work(self):
        for flags, env_value in ((["-O"], None), (["-OO"], None), ([], "1")):
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("PYTHONOPTIMIZE", None)
            if env_value is not None:
                env["PYTHONOPTIMIZE"] = env_value
            for name in (
                "hwmp24.py",
                "verify_hwmp24.py",
                "install_hwmp24.py",
                "prepare_workshop.py",
            ):
                with self.subTest(flags=flags, environment=env_value, tool=name):
                    result = subprocess.run(
                        [sys.executable, "-B", *flags, str(ROOT / "tools" / name), "--help"],
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("remove -O/-OO and PYTHONOPTIMIZE", result.stderr)

    def test_each_active_tool_has_early_guard(self):
        for path in (ROOT / "tools").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf8"))
            if path.name == "tool_safety.py":
                continue
            imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
            self.assertTrue(any(node.module == "tool_safety" for node in imports), path.name)

    def test_contexts_do_not_share_receipts_or_outputs(self):
        from build_paths import paths

        stable, candidate = paths(), paths(True)
        self.assertNotEqual(stable.work, candidate.work)
        self.assertNotEqual(stable.source, candidate.source)
        self.assertNotEqual(stable.release, candidate.release)

    def test_archive_root_restored_when_build_fails(self):
        import hwrm_archive as archive

        before = archive.ROOT
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(archive, "_package_source", side_effect=RuntimeError("injected")):
                with self.assertRaises(RuntimeError):
                    archive.package_source(folder, folder, "test.big", "test")
        self.assertEqual(archive.ROOT, before)

    def test_fresh_package_excludes_stale_files_and_preserves_backup(self):
        from package_promotion import promote
        import json

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / "work"
            work.mkdir()
            stage = work / "stage"
            stage.mkdir()
            target = root / "release"
            target.mkdir()
            (target / "version.json").write_text(json.dumps({"identity": "fixture"}))
            (target / "stale.txt").write_text("preserve outside new release")
            (stage / "new.txt").write_text("new")
            backup = promote(stage, target, work, root, "fixture", "first")
            self.assertFalse((target / "stale.txt").exists())
            self.assertTrue((backup / "stale.txt").is_file())
            self.assertTrue((target / "new.txt").is_file())

    def test_failed_package_promotion_restores_previous(self):
        from package_promotion import promote
        import json

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root / "work"
            work.mkdir()
            stage = work / "stage"
            stage.mkdir()
            target = root / "release"
            target.mkdir()
            (target / "version.json").write_text(json.dumps({"identity": "fixture"}))
            (target / "old.txt").write_text("old")
            original = Path.replace

            def fail_stage(path, destination):
                if path == stage:
                    raise OSError("injected promotion failure")
                return original(path, destination)

            with patch.object(Path, "replace", fail_stage):
                with self.assertRaises(OSError):
                    promote(stage, target, work, root, "fixture", "second")
            self.assertEqual((target / "old.txt").read_text(), "old")


class GeneratorTests(unittest.TestCase):
    def test_only_collector_count_changes(self):
        from hwmp24 import equal_collector_start

        source = 'type="Vgr_ResourceCollector", number=7, position={1,2,3}'
        self.assertEqual(equal_collector_start(source), source.replace("number=7", "number=6"))
        with self.assertRaises(AssertionError):
            equal_collector_start(source.replace("number=7", "number=6"))

    def test_quote_roundtrip_unicode_and_escapes(self):
        from hwmp24 import lua_quote
        from lupa.lua51 import LuaRuntime

        value = 'Авианосец "test"\n\\'
        self.assertEqual(LuaRuntime().eval(lua_quote(value)), value)

    def test_effect_generation_is_deterministic(self):
        from effect_journal import generate_effects

        self.assertEqual(generate_effects(), generate_effects())

    def test_effect_checkpoint_ownership_regressions(self):
        from effect_fixtures import vm_for_templates
        from verify_effect_journal import verify

        result = verify(vm_for_templates)
        self.assertEqual(result["status"], "passed")

    def test_installation_rollback_and_portable_receipt(self):
        from verify_installation import verify

        self.assertEqual(verify()["status"], "passed")

    def test_prose_check_preserves_identifiers_and_code(self):
        from prose_style import glued_prose

        self.assertEqual(glued_prose("HW2 Lua4 `build21` https://example.org/build21"), [])
        self.assertEqual(
            glued_prose("build21 Vaygr6/6 multiplier1.2 old2.4.1"),
            ["build21", "Vaygr6", "multiplier1", "old2"],
        )

    def test_document_links(self):
        from verify_documentation import verify

        self.assertEqual(verify()["status"], "passed")


if __name__ == "__main__":
    unittest.main()
