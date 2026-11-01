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
# - See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for validate_gaql skill script."""

import argparse
import io
import os
import sys
import unittest
from unittest import mock

# Add the scripts directory to sys.path to import validate_gaql
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
)

import validate_gaql
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


class TestValidateGaql(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = mock.create_autospec(GoogleAdsClient, instance=True)
        self.mock_service = mock.MagicMock()
        self.mock_client.get_service.return_value = self.mock_service

    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_validate_gaql_success(self, mock_stdout) -> None:
        validate_gaql.validate_gaql(
            customer_id="12345678",
            api_version="v23",
            query="SELECT campaign.id FROM campaign",
            client=self.mock_client,
        )
        self.mock_client.get_service.assert_called_once_with("GoogleAdsService")
        self.mock_service.search.assert_called_once()
        self.assertIn(
            "SUCCESS: GAQL query is structurally valid.", mock_stdout.getvalue()
        )

    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_validate_gaql_empty_query(self, mock_stdout) -> None:
        with self.assertRaises(SystemExit) as cm:
            validate_gaql.validate_gaql(
                customer_id="12345678",
                api_version="v23",
                query="",
                client=self.mock_client,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: No query provided.", mock_stdout.getvalue())

    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_validate_gaql_invalid_version_import(self, mock_stdout) -> None:
        with self.assertRaises(SystemExit) as cm:
            validate_gaql.validate_gaql(
                customer_id="12345678",
                api_version="v999",
                query="SELECT campaign.id FROM campaign",
                client=self.mock_client,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(
            "CRITICAL ERROR: Could not import SearchGoogleAdsRequest for v999.",
            mock_stdout.getvalue(),
        )

    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_validate_gaql_generic_exception(self, mock_stdout) -> None:
        self.mock_service.search.side_effect = ValueError("Unexpected failure")
        with self.assertRaises(SystemExit) as cm:
            validate_gaql.validate_gaql(
                customer_id="12345678",
                api_version="v23",
                query="SELECT campaign.id FROM campaign",
                client=self.mock_client,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("CRITICAL ERROR: Unexpected failure", mock_stdout.getvalue())

    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_validate_gaql_googleads_exception(self, mock_stdout) -> None:
        mock_error = mock.MagicMock()
        mock_error.message = "Invalid field."
        mock_error.location.field_path_elements = [
            mock.MagicMock(field_name="invalid_field")
        ]

        self.mock_service.search.side_effect = GoogleAdsException(
            error=mock.MagicMock(),
            failure=mock.MagicMock(errors=[mock_error]),
            request_id="dummy_req_id",
            call=mock.MagicMock(),
        )

        with self.assertRaises(SystemExit) as cm:
            validate_gaql.validate_gaql(
                customer_id="12345678",
                api_version="v23",
                query="SELECT invalid_field FROM campaign",
                client=self.mock_client,
            )
        self.assertEqual(cm.exception.code, 1)
        output = mock_stdout.getvalue()
        self.assertIn(
            "FAILURE: Query validation failed with Request ID dummy_req_id",
            output,
        )
        self.assertIn("  - Invalid field.", output)
        self.assertIn("    On field: invalid_field", output)

    @mock.patch.object(sys, "stdin", new_callable=io.StringIO)
    @mock.patch.object(argparse.ArgumentParser, "parse_args")
    @mock.patch.object(validate_gaql, "validate_gaql", autospec=True)
    def test_main(self, mock_validate_gaql, mock_parse_args, mock_stdin) -> None:
        mock_parse_args.return_value = argparse.Namespace(
            customer_id="12345678", api_version="v23"
        )
        mock_stdin.write("SELECT campaign.id FROM campaign")
        mock_stdin.seek(0)

        validate_gaql.main()

        mock_validate_gaql.assert_called_once_with(
            "12345678", "v23", "SELECT campaign.id FROM campaign"
        )


if __name__ == "__main__":
    unittest.main()
