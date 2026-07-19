import importlib.util
import os
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "wordpress-auto-publisher"
    / "wordpress-upload-images.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("wordpress_upload_images", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WordPressAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.original_password = os.environ.pop("WP_APP_PASSWORD", None)

    def tearDown(self):
        if self.original_password is not None:
            os.environ["WP_APP_PASSWORD"] = self.original_password

    def test_password_has_no_embedded_default(self):
        module = load_module()

        self.assertEqual(module.WP_APP_PASSWORD, "")
        with self.assertRaisesRegex(
            RuntimeError, "WP_APP_PASSWORD environment variable is required"
        ):
            module.get_wordpress_auth()

    def test_password_comes_from_environment(self):
        os.environ["WP_APP_PASSWORD"] = "test-only-password"
        module = load_module()

        self.assertEqual(
            module.get_wordpress_auth(), (module.WP_USER, "test-only-password")
        )


if __name__ == "__main__":
    unittest.main()
