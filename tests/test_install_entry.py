from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallEntryTests(unittest.TestCase):
    def run_install(self, home, *extra):
        return subprocess.run([sys.executable, str(ROOT/'scripts/install_skills.py'), '--agent', 'codex', '--agent-home', str(home), *extra], capture_output=True, text=True, encoding='utf-8')

    def test_dry_run_creates_no_agent_files(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)/'new agent'
            result = self.run_install(home, '--dry-run')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(home.exists())

    def test_collision_is_rejected_before_updating_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home/'skills/codoop-setup').mkdir(parents=True)
            sentinel = home/'codoop-plugins/codoop-cast/scripts/install_skills.py'
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text('previous installed version', encoding='utf-8')
            result = self.run_install(home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Refusing to overwrite', result.stderr)
            self.assertEqual(sentinel.read_text(encoding='utf-8'), 'previous installed version')
            self.assertFalse((sentinel.parents[1]/'runtime').exists())

    def test_upgrade_retires_only_owned_legacy_discovery_links(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            bundle = home/'codoop-plugins/codoop-cast'
            discovery = home/'skills'
            discovery.mkdir()
            old = bundle/'skills/codoop-cast-setup'
            old.mkdir(parents=True)
            try:
                (discovery/'codoop-cast-setup').symlink_to(old, target_is_directory=True)
                unrelated = home/'unrelated'
                unrelated.mkdir()
                (discovery/'codoop-cast-voice').symlink_to(unrelated, target_is_directory=True)
            except OSError as exc:
                self.skipTest('Symlink creation unavailable: '+str(exc))
            (discovery/'codoop-init').mkdir()  # Another plugin's entry remains untouched.
            result = self.run_install(home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((discovery/'codoop-cast-setup').is_symlink())
            self.assertEqual((discovery/'codoop-setup').resolve(), (bundle/'skills/codoop-setup').resolve())
            self.assertEqual((discovery/'codoop-cast-voice').resolve(), unrelated)
            self.assertTrue((discovery/'codoop-init').is_dir())
            self.assertEqual(self.run_install(home).returncode, 0)
            installed = subprocess.run([sys.executable, str(bundle/'scripts/install_skills.py'), '--agent', 'codex', '--agent-home', str(home)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertFalse((discovery/'codoop-cast-setup').is_symlink())
