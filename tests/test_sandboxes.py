import unittest
import os
from sandboxes.local_sandbox import LocalSandbox
from sandboxes.docker_sandbox import DockerSandbox


class TestSandboxes(unittest.TestCase):

    def test_local_sandbox_write_read_execute(self):
        sandbox = LocalSandbox(base_dir="/tmp/test_local_sandbox")
        sandbox.start()

        sandbox.write_file("test.txt", "hello sandbox")
        content = sandbox.read_file("test.txt")
        self.assertEqual(content, "hello sandbox")

        res = sandbox.execute_command("echo 'running command'")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("running command", res.stdout)

        sandbox.stop()

    def test_docker_sandbox_fallback(self):
        sandbox = DockerSandbox(workspace_path="/tmp/test_docker_sandbox")
        sandbox.start()
        sandbox.write_file("hello.py", "print('hello world')")
        content = sandbox.read_file("hello.py")
        self.assertEqual(content, "print('hello world')")
        sandbox.stop()


if __name__ == "__main__":
    unittest.main()
