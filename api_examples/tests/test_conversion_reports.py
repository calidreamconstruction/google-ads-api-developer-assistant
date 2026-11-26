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
from unittest.mock import MagicMock
from io import StringIO
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from api_examples.conversion_reports import _calculate_date_range, get_conversion_performance_report

class TestConversionReports(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_calculate_date_range_preset_last_10_days(self):
        start, end = _calculate_date_range(None, None, "LAST_10_DAYS")
        today = datetime.now()
        expected_start = (today - timedelta(days=10)).strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, today.strftime("%Y-%m-%d"))

    def test_get_conversion_performance_report_mapping(self):
        mock_row = MagicMock()
        mock_row.segments.date = "2026-02-24"
        mock_row.campaign.id = 999
        mock_row.campaign.name = "Opti Campaign"
        mock_row.metrics.conversions = 10.5

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]
        self.mock_ga_service.search_stream.return_value = [mock_batch]

        get_conversion_performance_report(
            self.mock_client, self.customer_id, "console", "", None, None, "LAST_7_DAYS",
            ["conversions"], [], None
        )

        output = self.captured_output.getvalue()
        self.assertIn("Opti Campaign", output)
        self.assertIn("10.5", output)

if __name__ == "__main__":
    unittest.main()
