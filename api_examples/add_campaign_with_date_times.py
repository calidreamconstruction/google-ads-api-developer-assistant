#!/usr/bin/env python
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

"""This example demonstrates how to create a campaign with start and end date times.

This feature was added in v23 of the Google Ads API.
"""

import argparse
import sys
import uuid
from datetime import datetime, timedelta

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def main(client, customer_id):
    """The main method that creates all necessary entities for the example.

    Args:
        client: an initialized GoogleAdsClient instance.
        customer_id: a client customer ID.
    """
    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_service = client.get_service("CampaignService")

    # Create a budget, which is a required constraint when creating a campaign.
    campaign_budget_operation = client.get_type("CampaignBudgetOperation")
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"Interplanetary Budget {uuid.uuid4()}"
    campaign_budget.delivery_method = (
        client.enums.BudgetDeliveryMethodEnum.STANDARD
    )
    campaign_budget.amount_micros = 500000

    # Add budget.
    try:
        campaign_budget_response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id, operations=[campaign_budget_operation]
        )
    except GoogleAdsException as ex:
        _handle_google_ads_exception(ex)

    campaign_budget_resource_name = campaign_budget_response.results[0].resource_name
    print(
        f"Created campaign budget with resource name: '{campaign_budget_resource_name}'"
    )

    # Create campaign.
    campaign_operation = client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = f"Interplanetary Cruise Campaign {uuid.uuid4()}"
    campaign.advertising_channel_type = (
        client.enums.AdvertisingChannelTypeEnum.SEARCH
    )

    # Recommendation: Set the campaign to PAUSED when creating it to prevent
    # the ads from immediately serving.
    campaign.status = client.enums.CampaignStatusEnum.PAUSED

    # Set the budget.
    campaign.campaign_budget = campaign_budget_resource_name

    # Set the network settings.
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_content_network = False
    campaign.network_settings.target_partner_search_network = False

    # Optional: Set the start date time and end date time.
    # Note: These fields are only available in v23 and later.
    # The format must be 'yyyy-mm-dd hh:mm:ss'.
    # We will set the start time to 1 day from now, and end time to 30 days from now.
    now = datetime.now()
    start_time = now + timedelta(days=1)
    end_time = now + timedelta(days=31)

    campaign.start_date_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
    campaign.end_date_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

    # Add the campaign.
    try:
        campaign_response = campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_operation]
        )
        print(
            f"Created campaign with resource name: '{campaign_response.results[0].resource_name}'"
        )
        print(f"Start date time: {campaign.start_date_time}")
        print(f"End date time: {campaign.end_date_time}")
    except GoogleAdsException as ex:
        _handle_google_ads_exception(ex)


def _handle_google_ads_exception(exception):
    """Prints the details of a GoogleAdsException object.

    Args:
        exception: an instance of GoogleAdsException.
    """
    print(
        f"Request with ID '{exception.request_id}' failed with status "
        f"'{exception.error.code().name}' and includes the following errors:"
    )
    for error in exception.failure.errors:
        print(f"\tError with message '{error.message}'.")
        if error.location:
            for field_path_element in error.location.field_path_elements:
                print(f"\t\tOn field: {field_path_element.field_name}")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a campaign with start and end date times."
    )
    # The following argument(s) are required to run the example.
    parser.add_argument(
        "-c",
        "--customer_id",
        type=str,
        required=True,
        help="The Google Ads customer ID.",
    )
    parser.add_argument(
        "-v",
        "--api_version",
        type=str,
        required=True,
        help="The Google Ads API version.",
    )
    args = parser.parse_args()

    # GoogleAdsClient will read the google-ads.yaml configuration file in the
    # home directory if none is specified.
    googleads_client = GoogleAdsClient.load_from_storage(version=args.api_version)

    main(googleads_client, args.customer_id)
