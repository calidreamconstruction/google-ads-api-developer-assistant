# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add the project root to sys.path so we can import the hook scripts
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
hooks_dir = os.path.join(project_root, ".gemini/hooks")
sys.path.append(hooks_dir)

import configure_environment  # noqa: E402

class TestConfigureEnvironment(unittest.TestCase):

    def test_get_version_success(self):
        with patch("subprocess.run") as mocked_run:
            mocked_run.return_value = MagicMock(stdout="2.1.0\n", check=True)
            version = configure_environment.get_version("dummy_script.py")
            self.assertEqual(version, "2.1.0")
            mocked_run.assert_called_once()

    def test_get_version_failure(self):
        with patch("subprocess.run") as mocked_run:
            mocked_run.side_effect = Exception("failed")
            version = configure_environment.get_version("dummy_script.py")
            self.assertEqual(version, "666")  # Fallback



    def test_parse_ruby_config(self):
        content = """
        c.developer_token = 'token123'
        c.client_id = "id456"
        c.client_secret = 'secret789'
        """
        with patch("builtins.open", mock_open(read_data=content)):
            data = configure_environment.parse_ruby_config("dummy.rb")
            self.assertEqual(data["developer_token"], "token123")
            self.assertEqual(data["client_id"], "id456")
            self.assertEqual(data["client_secret"], "secret789")

    def test_parse_ini_config(self):
        content = "[DEFAULT]\ndeveloperToken = token123\nclientId = 'id456'\n"
        with patch("builtins.open", mock_open(read_data=content)):
            data = configure_environment.parse_ini_config("dummy.ini")
            self.assertEqual(data["developer_token"], "token123")
            self.assertEqual(data["client_id"], "id456")

    def test_parse_properties_config(self):
        content = "api.googleads.developerToken=token123\napi.googleads.clientId=id456\n"
        with patch("builtins.open", mock_open(read_data=content)):
            data = configure_environment.parse_properties_config("dummy.properties")
            self.assertEqual(data["developer_token"], "token123")
            self.assertEqual(data["client_id"], "id456")

    def test_write_yaml_config_oauth2(self):
        data = {
            "developer_token": "token123",
            "client_id": "id456",
            "client_secret": "secret789",
            "refresh_token": "refresh000"
        }
        with patch("builtins.open", mock_open()) as mocked_file:
            success = configure_environment.write_yaml_config(data, "dummy.yaml")
            self.assertTrue(success)
            handle = mocked_file()
            handle.write.assert_any_call("developer_token: token123\n")
            handle.write.assert_any_call("client_id: id456\n")

    def test_write_yaml_config_service_account(self):
        data = {
            "developer_token": "token123",
            "json_key_file_path": "/path/to/key.json",
            "impersonated_email": "user@example.com"
        }
        with patch("builtins.open", mock_open()) as mocked_file:
            success = configure_environment.write_yaml_config(data, "dummy.yaml")
            self.assertTrue(success)
            handle = mocked_file()
            handle.write.assert_any_call("json_key_file_path: /path/to/key.json\n")
            handle.write.assert_any_call("impersonated_email: user@example.com\n")
            # Verify client_id is NOT written
            for call in handle.write.call_args_list:
                self.assertNotIn("client_id:", call[0][0])

    def test_copy_and_append_version(self):
        with patch("os.path.exists", return_value=True), \
             patch("shutil.copy2") as mocked_copy, \
             patch("builtins.open", mock_open()) as mocked_file:
            success = configure_environment.copy_and_append_version("home.yaml", "target.yaml", "2.1.0")
            self.assertTrue(success)
            mocked_copy.assert_called_once_with("home.yaml", "target.yaml")
            
            handle = mocked_file()
            handle.write.assert_called_once_with("\nads_assistant: 2.1.0\n")

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock_open)
    def test_manage_policy_file_creates_new(self, mock_file, mock_exists, mock_makedirs):
        with patch("os.path.expanduser", return_value="/mock/home"):
            configure_environment.manage_policy_file()
            mock_makedirs.assert_called_once_with("/mock/home/.gemini/policies", exist_ok=True)
            mock_file.assert_called_once_with("/mock/home/.gemini/policies/ads_assistant.toml", "w")
            handle = mock_file()
            written = "".join(call[0][0] for call in handle.write.call_args_list)
            self.assertIn('toolName = ["save_memory"]', written)
            self.assertIn('decision = "deny"', written)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=True)
    def test_manage_policy_file_appends(self, mock_exists, mock_makedirs):
        existing_content = '[[rule]]\ntoolName = ["other"]\ndecision = "allow"\n'
        with patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:
            with patch("os.path.expanduser", return_value="/mock/home"):
                configure_environment.manage_policy_file()
                handle = mock_file()
                written = "".join(call[0][0] for call in handle.write.call_args_list)
                self.assertIn('toolName = ["other"]', written)
                self.assertIn('toolName = ["save_memory"]', written)
                self.assertIn('decision = "deny"', written)

    @patch("os.makedirs")
    @patch("os.path.exists", return_value=True)
    def test_manage_policy_file_replaces(self, mock_exists, mock_makedirs):
        existing_content = '[[rule]]\ntoolName = ["save_memory"]\ndecision = "allow"\n[[rule]]\ntoolName = ["other"]\n'
        with patch("builtins.open", mock_open(read_data=existing_content)) as mock_file:
            with patch("os.path.expanduser", return_value="/mock/home"):
                configure_environment.manage_policy_file()
                handle = mock_file()
                written = "".join(call[0][0] for call in handle.write.call_args_list)
                self.assertIn('toolName = ["save_memory"]', written)
                self.assertIn('decision = "deny"', written)
                self.assertNotIn('decision = "allow"', written)
                self.assertIn('toolName = ["other"]', written)

    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_create_virtual_env_success(self, mock_run, mock_exists):
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)
        
        configure_environment.create_virtual_env("/mock/root")
        
        mock_exists.assert_called_once_with("/mock/root/.venv")
        self.assertEqual(mock_run.call_count, 2)
        
        called_args = [call[0][0] for call in mock_run.call_args_list]
        # First call: venv creation
        self.assertIn("-m", called_args[0])
        self.assertIn("venv", called_args[0])
        # Second call: pip install
        self.assertIn("install", called_args[1])
        self.assertIn("google-ads", called_args[1])

    @patch("builtins.print")
    def test_finish_hook_custom_vars(self, mock_print):
        import json
        with patch("os.environ", {"PATH": "/usr/bin"}):
            configure_environment.finish_hook("/mock/target.yaml", "2.1.0")
            
            mock_print.assert_called_once()
            args, kwargs = mock_print.call_args
            data = json.loads(args[0])
            self.assertIn("custom_vars", data)
            self.assertEqual(data["custom_vars"]["ads_assistant"], "2.1.0")
            self.assertEqual(data["custom_vars"]["GOOGLE_ADS_CONFIGURATION_FILE_PATH"], "/mock/target.yaml")
            self.assertIn(".venv/bin", data["custom_vars"]["PATH"])

if __name__ == "__main__":
    unittest.main()
