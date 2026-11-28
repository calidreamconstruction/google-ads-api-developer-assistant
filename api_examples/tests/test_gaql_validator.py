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

from api_examples.gaql_validator import main

class TestGAQLValidator(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.api_version = "v23"
        self.test_query = "SELECT campaign.id FROM campaign"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("importlib.import_module")
    def test_main_success(self, mock_import):
        mock_module = MagicMock()
        mock_import.return_value = mock_module
        mock_request_class = MagicMock()
        setattr(mock_module, "SearchGoogleAdsRequest", mock_request_class)

        main(client=self.mock_client, customer_id=self.customer_id, api_version=self.api_version, query=self.test_query)

        self.mock_ga_service.search.assert_called_once()
        output = self.captured_output.getvalue()
        self.assertIn("[DRY RUN]", output)
        self.assertIn("SUCCESS: GAQL query is structurally valid.", output)

if __name__ == "__main__":
    unittest.main()
