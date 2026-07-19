from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class SkillIndexTest(unittest.TestCase):
    def test_readme_lists_every_skill_directory(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        skill_names = sorted(
            path.name for path in (ROOT / "skills").iterdir() if path.is_dir()
        )

        for skill_name in skill_names:
            with self.subTest(skill=skill_name):
                self.assertIn(f"`{skill_name}`", readme)


if __name__ == "__main__":
    unittest.main()
