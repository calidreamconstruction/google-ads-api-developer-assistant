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
from unittest.mock import patch

# Add the project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
hooks_dir = os.path.join(project_root, ".gemini/hooks")
sys.path.append(hooks_dir)

import cleanup_environment  # noqa: E402

class TestCleanupEnvironment(unittest.TestCase):

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("os.unlink")
    @patch("shutil.rmtree")
    def test_cleanup_success(self, mock_rmtree, mock_unlink, mock_isdir, mock_isfile, mock_listdir, mock_exists):
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.txt", "dir1", ".gitkeep"]
        
        # Define side effects for isfile and isdir
        def is_file_side_effect(path):
            return "file1.txt" in path
        def is_dir_side_effect(path):
            return "dir1" in path
            
        mock_isfile.side_effect = is_file_side_effect
        mock_isdir.side_effect = is_dir_side_effect

        cleanup_environment.cleanup()

        # Verify calls
        mock_unlink.assert_called_once()
        self.assertIn("file1.txt", mock_unlink.call_args[0][0])
        
        self.assertEqual(mock_rmtree.call_count, 2)
        called_dirs = [call[0][0] for call in mock_rmtree.call_args_list]
        self.assertTrue(any("dir1" in d for d in called_dirs))
        self.assertTrue(any(".venv" in d for d in called_dirs))
        
        # Verify .gitkeep was NOT touched
        for call in mock_unlink.call_args_list:
            self.assertNotIn(".gitkeep", call[0][0])

    @patch("os.path.exists")
    def test_cleanup_no_config_dir(self, mock_exists):
        mock_exists.return_value = False
        with patch("sys.stderr") as mock_stderr:
            cleanup_environment.cleanup()
            mock_stderr.write.assert_called()
            # Should not call listdir if it doesn't exist
            with patch("os.listdir") as mock_listdir:
                cleanup_environment.cleanup()
                mock_listdir.assert_not_called()

if __name__ == "__main__":
    unittest.main()
