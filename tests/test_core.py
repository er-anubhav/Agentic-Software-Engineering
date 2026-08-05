import unittest
import os
from core.config import get_settings
from core.container import get_container


class TestCore(unittest.TestCase):

    def test_settings_defaults(self):
        settings = get_settings()
        self.assertEqual(settings.app_name, "Agentic Software Engineering Platform")
        self.assertEqual(settings.version, "2.0.0-alpha")
        self.assertTrue(os.path.exists(settings.repository_path))

    def test_container_singleton(self):
        c1 = get_container()
        c2 = get_container()
        self.assertIs(c1, c2)
        self.assertIsNotNone(c1.settings)


if __name__ == "__main__":
    unittest.main()
