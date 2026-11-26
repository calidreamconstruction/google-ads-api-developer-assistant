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

"""Reports disapproved ads with policy topic details."""

import argparse
import csv

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def main(client: GoogleAdsClient, customer_id: str, output_file: str) -> None:
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT campaign.id, campaign.name, ad_group_ad.ad.id,
               ad_group_ad.policy_summary.approval_status,
               ad_group_ad.policy_summary.policy_topic_entries
        FROM ad_group_ad
        WHERE ad_group_ad.policy_summary.approval_status = 'DISAPPROVED'"""

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        rows = []
        for batch in stream:
            for row in batch.results:
                policy_entries = row.ad_group_ad.policy_summary.policy_topic_entries
                topics = [
                    entry.topic
                    for entry in policy_entries
                    if entry.type_.name == "PROHIBITED"
                ]
                rows.append(
                    [
                        row.campaign.id,
                        row.campaign.name,
                        row.ad_group_ad.ad.id,
                        row.ad_group_ad.policy_summary.approval_status.name,
                        "; ".join(topics),
                    ]
                )

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Campaign ID", "Campaign", "Ad ID", "Status", "Topics"]
            )
            writer.writerows(rows)
        print(f"Disapproved ads report written to {output_file}")
    except GoogleAdsException as ex:
        for error in ex.failure.errors:
            print(f"Error: {error.message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--customer_id", required=True)
    parser.add_argument(
        "-o", "--output", default="saved/csv/disapproved_ads.csv"
    )
    parser.add_argument(
        "-v",
        "--api_version",
        type=str,
        required=True,
        help="The Google Ads API version.",
    )
    args = parser.parse_args()
    client = GoogleAdsClient.load_from_storage(version=args.api_version)
    main(client, args.customer_id, args.output)