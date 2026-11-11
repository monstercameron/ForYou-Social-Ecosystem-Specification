"""Prevent ambiguous lowercase requirement keywords in specification documents."""
import re
import unittest
from pathlib import Path


class NormativeLanguageTests(unittest.TestCase):
    def test_no_lowercase_requirement_modals(self):
        docs = Path(__file__).resolve().parents[1] / 'docs'
        violations = []
        for path in sorted(docs.glob('*.md')):
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if re.search(r'\b(?:must|should)\b|\b(?:MUST|SHOULD) not\b', line):
                    violations.append(f'{path.name}:{number}')
        self.assertEqual(violations, [], 'Lowercase requirement modal(s): ' + ', '.join(violations))


if __name__ == '__main__':
    unittest.main()
