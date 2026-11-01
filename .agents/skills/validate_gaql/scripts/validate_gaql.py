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

"""GAQL Query Validator Skill.

This script performs a dry-run validation of a GAQL query using the
validate_only=True parameter. It reads the query from stdin to avoid
shell-escaping issues with complex SQL strings.
"""

import argparse
import importlib
import re
import sys
from typing import Optional

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def handle_googleads_exception(exception: GoogleAdsException) -> None:
    """Prints the details of a GoogleAdsException.

    Args:
        exception: An exception of type GoogleAdsException.
    """
    print(f"FAILURE: Query validation failed with Request ID {exception.request_id}")
    for error in exception.failure.errors:
        print(f"  - {error.message}")
        if error.location:
            for element in error.location.field_path_elements:
                print(f"    On field: {element.field_name}")


def validate_gaql(
    customer_id: str,
    api_version: str,
    query: str,
    client: Optional[GoogleAdsClient] = None,
) -> None:
    """Validates a GAQL query by performing a dry run against the API.

    Args:
        customer_id: The Google Ads customer ID.
        api_version: The API version to use (e.g., "v23").
        query: The GAQL query to validate.
        client: An optional GoogleAdsClient instance.
    """
    if client is None:
        try:
            client = GoogleAdsClient.load_from_storage(version=api_version)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to load Google Ads configuration: {e}")
            sys.exit(1)

    if not query:
        print("Error: No query provided.")
        sys.exit(1)

    # Static Analysis
    query_upper = query.upper()
    has_from = " FROM " in query_upper or query_upper.strip().startswith("SELECT") and "FROM" in query_upper

    # Check for metadata query pitfalls
    if "GOOGLE_ADS_FIELD" in query_upper:
        if has_from:
            print("FAILURE: Metadata queries (google_ads_field) MUST NOT contain a FROM clause.")
            print("  - Incorrect: SELECT name FROM google_ads_field")
            print("  - Correct: SELECT name")
            sys.exit(1)
        if any(prefix in query_upper for prefix in ["GOOGLE_ADS_FIELD.", "METRICS.", "SEGMENTS."]):
            print("FAILURE: Metadata queries MUST NOT use resource/segment prefixes (e.g., use 'name', not 'google_ads_field.name').")
            sys.exit(1)

    # Dynamically handle versioned types for the request object
    api_version_lower = api_version.lower()
    module_path = (
        f"google.ads.googleads.{api_version_lower}.services.types.google_ads_service"
    )
    try:
        module = importlib.import_module(module_path)
        search_request_type = getattr(module, "SearchGoogleAdsRequest")
    except (ImportError, AttributeError):
        print(
            f"CRITICAL ERROR: Could not import SearchGoogleAdsRequest for {api_version}."
        )
        sys.exit(1)

    ga_service = client.get_service("GoogleAdsService")
    # Normalize customer_id to digits only
    clean_customer_id = "".join(re.findall(r"\d+", str(customer_id)))

    try:
        print(f"--- [DRY RUN] Validating Query for {clean_customer_id} ---")
        request = search_request_type(
            customer_id=clean_customer_id, query=query, validate_only=True
        )
        ga_service.search(request=request)
        print("SUCCESS: GAQL query is structurally valid.")
    except GoogleAdsException as ex:
        handle_googleads_exception(ex)
        sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)


def main() -> None:
    """Parses command line arguments and calls validate_gaql."""
    parser = argparse.ArgumentParser(description="Validates a GAQL query.")
    parser.add_argument("--customer_id", required=True, help="Google Ads Customer ID.")
    parser.add_argument(
        "--api_version",
        required=True,
        help="API Version (e.g., v23).",
    )
    args = parser.parse_args()

    # Read query from stdin to handle multiline/quoted strings safely
    query = sys.stdin.read().strip()

    validate_gaql(args.customer_id, args.api_version, query)


if __name__ == "__main__":
    main()
