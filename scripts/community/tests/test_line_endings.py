"""Hash-pinned artifacts and POSIX scripts must keep exact bytes in every checkout."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LF_REQUIRED = (
    'dev',
    '.githooks/pre-commit',
    'scripts/security/install-gitleaks.sh',
    'research/acbsd/examples/smoke-v1/events.jsonl',
    'research/acbsd/examples/smoke-v1/ground_truth.jsonl',
    'community/reporting/fixtures/snapshots/source-evidence.json',
)


def git(*args):
    return subprocess.run(('git', *args), cwd=ROOT, check=True, capture_output=True, text=True).stdout


class LineEndingTests(unittest.TestCase):
    def test_hash_pinned_paths_are_declared_lf(self):
        for path in LF_REQUIRED:
            with self.subTest(path=path):
                self.assertEqual(git('check-attr', 'eol', '--', path).split(': ')[-1].strip(), 'lf')

    def test_no_tracked_text_is_converted_on_checkout(self):
        converted = [line for line in git('ls-files', '--eol').splitlines()
                     if line.startswith('i/lf') and line.split()[1] != 'w/lf']
        self.assertEqual(converted, [])


if __name__ == '__main__':
    unittest.main()
