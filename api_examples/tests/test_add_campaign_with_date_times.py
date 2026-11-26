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

import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Import the main function from the example script
from api_examples import add_campaign_with_date_times

class TestAddCampaignWithDateTimes(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.customer_id = "1234567890"

    def test_main(self):
        # Mock services
        mock_campaign_budget_service = MagicMock()
        mock_campaign_service = MagicMock()
        
        def get_service_side_effect(service_name):
            if service_name == "CampaignBudgetService":
                return mock_campaign_budget_service
            elif service_name == "CampaignService":
                return mock_campaign_service
            return MagicMock()
            
        self.mock_client.get_service.side_effect = get_service_side_effect
        
        # Mock types
        mock_campaign_budget_operation = MagicMock()
        mock_campaign_operation = MagicMock()
        
        def get_type_side_effect(type_name):
            if type_name == "CampaignBudgetOperation":
                return mock_campaign_budget_operation
            elif type_name == "CampaignOperation":
                return mock_campaign_operation
            return MagicMock()
            
        self.mock_client.get_type.side_effect = get_type_side_effect
        
        # Mock Enums
        self.mock_client.enums.BudgetDeliveryMethodEnum.STANDARD = "STANDARD"
        self.mock_client.enums.AdvertisingChannelTypeEnum.SEARCH = "SEARCH"
        self.mock_client.enums.CampaignStatusEnum.PAUSED = "PAUSED"
        
        # Mock responses
        mock_budget_response = MagicMock()
        mock_budget_response.results = [MagicMock(resource_name="budget_resource_name")]
        mock_campaign_budget_service.mutate_campaign_budgets.return_value = mock_budget_response
        
        mock_campaign_response = MagicMock()
        mock_campaign_response.results = [MagicMock(resource_name="campaign_resource_name")]
        mock_campaign_service.mutate_campaigns.return_value = mock_campaign_response
        
        # Run main
        add_campaign_with_date_times.main(self.mock_client, self.customer_id)
        
        # Asserts
        mock_campaign_budget_service.mutate_campaign_budgets.assert_called_once()
        mock_campaign_service.mutate_campaigns.assert_called_once()
        
        # Check if created campaign has start_date_time and end_date_time set
        created_campaign = mock_campaign_operation.create
        self.assertTrue(hasattr(created_campaign, "start_date_time"))
        self.assertTrue(hasattr(created_campaign, "end_date_time"))
        self.assertIsNotNone(created_campaign.start_date_time)
        self.assertIsNotNone(created_campaign.end_date_time)

if __name__ == "__main__":
    unittest.main()
