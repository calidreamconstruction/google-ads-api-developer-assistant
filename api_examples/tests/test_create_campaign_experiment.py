
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import unittest
from unittest.mock import MagicMock, patch

from google.ads.googleads.client import GoogleAdsClient

from api_examples.create_campaign_experiment import (
    create_experiment_resource,
    create_experiment_arms,
    modify_treatment_campaign,
)

# Import functions from the script


class MockMutateExperimentArmsRequest:
    def __init__(self):
        self.customer_id = None
        self.operations = []
        self.response_content_type = None


class TestCreateCampaignExperiment(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_experiment_service = MagicMock()
        self.mock_campaign_service = MagicMock()
        self.mock_experiment_arm_service = MagicMock()

        self.mock_client.enums = MagicMock()
        self.mock_client.enums.ExperimentTypeEnum = MagicMock()
        self.mock_client.enums.ExperimentTypeEnum.SEARCH_CUSTOM = 1
        self.mock_client.enums.ExperimentStatusEnum.SETUP = 1
        self.mock_client.enums.ResponseContentTypeEnum.MUTABLE_RESOURCE = 1

        self.customer_id = "1234567890"
        self.base_campaign_id = "111222333"

    def test_create_experiment_resource(self):
        mock_uuid = MagicMock()
        mock_uuid.uuid4.return_value = "test-uuid"
        with patch("api_examples.create_campaign_experiment.uuid", mock_uuid):
            mock_experiment_service = MagicMock()
            self.mock_client.get_service.return_value = mock_experiment_service

            mock_experiment_operation = MagicMock()
            mock_experiment = MagicMock()
            mock_experiment_operation.create = mock_experiment
            self.mock_client.get_type.return_value = mock_experiment_operation

            expected_resource_name = "customers/1234567890/experiments/98765"
            mock_response = MagicMock()
            mock_response.results = [MagicMock(resource_name=expected_resource_name)]
            mock_experiment_service.mutate_experiments.return_value = mock_response

            resource_name = create_experiment_resource(
                self.mock_client, self.customer_id
            )

            self.mock_client.get_service.assert_called_once_with("ExperimentService")
            self.mock_client.get_type.assert_called_once_with("ExperimentOperation")
            mock_experiment_service.mutate_experiments.assert_called_once_with(
                customer_id=self.customer_id, operations=[mock_experiment_operation]
            )
            self.assertEqual(resource_name, expected_resource_name)

    def test_create_experiment_arms(self):
        mock_campaign_service = MagicMock()
        mock_experiment_arm_service = MagicMock()

        self.mock_client.get_service.side_effect = [
            mock_campaign_service,  # For CampaignService
            mock_experiment_arm_service,  # For ExperimentArmService
        ]

        mock_experiment_arm_operation = MagicMock()
        mock_experiment_arm = MagicMock()
        mock_experiment_arm_operation.create = mock_experiment_arm

        mock_mutate_experiment_arms_request = MockMutateExperimentArmsRequest()

        self.mock_client.get_type.side_effect = [
            mock_experiment_arm_operation,  # For control arm
            mock_experiment_arm_operation,  # For treatment arm
            mock_mutate_experiment_arms_request,  # For MutateExperimentArmsRequest
        ]

        expected_draft_campaign_resource_name = (
            "customers/1234567890/campaigns/999888777"
        )
        mock_mutate_response = MagicMock()
        mock_control_arm_result = MagicMock(resource_name="control_arm_resource_name")
        mock_treatment_arm_result = MagicMock(
            resource_name="treatment_arm_resource_name"
        )
        mock_treatment_arm_result.experiment_arm.in_design_campaigns = [
            expected_draft_campaign_resource_name
        ]
        mock_mutate_response.results = [
            mock_control_arm_result,
            mock_treatment_arm_result,
        ]
        mock_experiment_arm_service.mutate_experiment_arms.return_value = (
            mock_mutate_response
        )

        mock_campaign_service.campaign_path.return_value = (
            "customers/1234567890/campaigns/111222333"
        )

        experiment_resource_name = "customers/1234567890/experiments/98765"
        draft_campaign_resource_name = create_experiment_arms(
            self.mock_client,
            self.customer_id,
            self.base_campaign_id,
            experiment_resource_name,
        )

        self.assertEqual(self.mock_client.get_service.call_count, 2)
        self.mock_client.get_service.assert_any_call("CampaignService")
        self.mock_client.get_service.assert_any_call("ExperimentArmService")

        self.assertEqual(self.mock_client.get_type.call_count, 3)
        mock_campaign_service.campaign_path.assert_called_once_with(
            self.customer_id, self.base_campaign_id
        )
        mock_experiment_arm_service.mutate_experiment_arms.assert_called_once()
        self.assertEqual(
            draft_campaign_resource_name, expected_draft_campaign_resource_name
        )

    @patch("api_examples.create_campaign_experiment.uuid")
    @patch("api_examples.create_campaign_experiment.protobuf_helpers.field_mask")
    def test_modify_treatment_campaign(self, mock_field_mask, mock_uuid):
        mock_uuid.uuid4.return_value = "test-uuid"

        mock_campaign_service = MagicMock()
        self.mock_client.get_service.return_value = mock_campaign_service

        mock_campaign_operation = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign_operation.update = mock_campaign
        self.mock_client.get_type.return_value = mock_campaign_operation

        draft_campaign_resource_name = "customers/1234567890/campaigns/999888777"

        mock_mutate_response = MagicMock()
        mock_campaign_service.mutate_campaigns.return_value = mock_mutate_response

        mock_field_mask.return_value = "field_mask_value"

        modify_treatment_campaign(
            self.mock_client, self.customer_id, draft_campaign_resource_name
        )

        self.mock_client.get_service.assert_called_once_with("CampaignService")
        self.mock_client.get_type.assert_called_once_with("CampaignOperation")
        mock_campaign_service.mutate_campaigns.assert_called_once_with(
            customer_id=self.customer_id, operations=[mock_campaign_operation]
        )
        self.mock_client.copy_from.assert_called_once()
