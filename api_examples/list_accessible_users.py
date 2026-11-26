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
"""Lists accessible customers with management context."""

import argparse

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main(client: GoogleAdsClient) -> None:
    """The main function to list accessible customers.

    Args:
        client: An initialized GoogleAdsClient instance.
    """
    customer_service = client.get_service("CustomerService")
    try:
        accessible = customer_service.list_accessible_customers()
        print(f"Found {len(accessible.resource_names)} accessible customers.")
        for rn in accessible.resource_names:
            print(f"- {rn}")
    except GoogleAdsException as ex:
        print(f"Request ID {ex.request_id} failed: {ex.error.code().name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lists accessible customers.")
    parser.add_argument(
        "-v", "--api_version", type=str, required=True, help="The Google Ads API version."
    )
    args = parser.parse_args()

    # GoogleAdsClient will read the google-ads.yaml configuration file in the
    # home directory if none is specified.
    googleads_client = GoogleAdsClient.load_from_storage(version=args.api_version)

    main(googleads_client)
