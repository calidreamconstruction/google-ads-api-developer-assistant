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

# Copyright 2026 Google LLC
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from api_examples.list_accessible_users import main

class TestListAccessibleUsers(unittest.TestCase):
    def setUp(self):
        self.captured_output = StringIO()
        self.sys_stdout = sys.stdout
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = self.sys_stdout

    @patch("api_examples.list_accessible_users.GoogleAdsClient.load_from_storage")
    def test_main_success(self, mock_load):
        mock_client = MagicMock()
        mock_load.return_value = mock_client
        mock_service = MagicMock()
        mock_client.get_service.return_value = mock_service
        
        mock_accessible = MagicMock()
        mock_accessible.resource_names = ["customers/1", "customers/2"]
        mock_service.list_accessible_customers.return_value = mock_accessible
        
        main(mock_client)
        output = self.captured_output.getvalue()
        self.assertIn("Found 2 accessible customers.", output)
        self.assertIn("customers/1", output)

if __name__ == "__main__":
    unittest.main()
