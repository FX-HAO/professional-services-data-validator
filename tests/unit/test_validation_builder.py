# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from copy import deepcopy

import pytest

from data_validation import consts
from data_validation.config_manager import ConfigManager


COLUMN_VALIDATION_CONFIG = {
    # BigQuery Specific Connection Config
    "source_conn": None,
    "target_conn": None,
    # Validation Type
    consts.CONFIG_TYPE: "Column",
    # Configuration Required Depending on Validator Type
    consts.CONFIG_SCHEMA_NAME: "bigquery-public-data.new_york_citibike",
    consts.CONFIG_TABLE_NAME: "citibike_trips",
    consts.CONFIG_GROUPED_COLUMNS: [],
    consts.CONFIG_FILTERS: [
        {
            consts.CONFIG_TYPE: consts.FILTER_TYPE_CUSTOM,
            consts.CONFIG_FILTER_SOURCE: "column_name > 100",
            consts.CONFIG_FILTER_TARGET: "column_name_target > 100",
        }
    ],
}

QUERY_LIMIT = 100
COLUMN_VALIDATION_CONFIG_LIMIT = deepcopy(COLUMN_VALIDATION_CONFIG)
COLUMN_VALIDATION_CONFIG_LIMIT[consts.CONFIG_LIMIT] = QUERY_LIMIT

QUERY_GROUPS_TEST = [
    {
        consts.CONFIG_FIELD_ALIAS: "start_alias",
        consts.CONFIG_SOURCE_COLUMN: "starttime",
        consts.CONFIG_TARGET_COLUMN: "starttime",
        consts.CONFIG_CAST: "date",
    }
]

AGGREGATES_TEST = [
    {
        consts.CONFIG_FIELD_ALIAS: "sum_starttime",
        consts.CONFIG_SOURCE_COLUMN: "starttime",
        consts.CONFIG_TARGET_COLUMN: "starttime",
        consts.CONFIG_TYPE: "sum",
    }
]

CALCULATED_MULTIPLE_TEST = [
    {
        consts.CONFIG_FIELD_ALIAS: "concat_start_station_name_end_station_name",
        consts.CONFIG_SOURCE_CALCULATED_COLUMNS: ["start_station_name", "end_station_name"],
        consts.CONFIG_TARGET_CALCULATED_COLUMNS: ["start_station_name", "end_station_name"],
        consts.CONFIG_TYPE: "concat",
    },
]


class MockIbisClient(object):
    pass


@pytest.fixture
def module_under_test():
    import data_validation.validation_builder

    return data_validation.validation_builder


def test_import(module_under_test):
    assert module_under_test is not None


def test_column_validation(module_under_test):
    mock_config_manager = ConfigManager(
        COLUMN_VALIDATION_CONFIG, MockIbisClient(), MockIbisClient(), verbose=False
    )
    builder = module_under_test.ValidationBuilder(mock_config_manager)

    assert not builder.verbose
    assert builder.config_manager.query_limit is None


def test_column_validation_aggregates(module_under_test):
    mock_config_manager = ConfigManager(
        COLUMN_VALIDATION_CONFIG, MockIbisClient(), MockIbisClient(), verbose=False
    )
    builder = module_under_test.ValidationBuilder(mock_config_manager)

    mock_config_manager.append_aggregates(AGGREGATES_TEST)
    builder.add_config_aggregates()

    assert list(builder.get_metadata().keys()) == ["sum_starttime"]


def test_validation_add_groups(module_under_test):
    mock_config_manager = ConfigManager(
        COLUMN_VALIDATION_CONFIG, MockIbisClient(), MockIbisClient(), verbose=False
    )
    builder = module_under_test.ValidationBuilder(mock_config_manager)

    mock_config_manager.append_query_groups(QUERY_GROUPS_TEST)
    builder.add_config_query_groups()

    assert list(builder.get_group_aliases()) == ["start_alias"]

def test_column_validation_calculate(module_under_test):
    mock_config_manager = ConfigManager(
        )
    builder = module_under_test.ValidationBuilder(mock_config_manager)

    mock_config_manager.append_calculated_fields(CALCULATED_MULTIPLE_TEST)
    builder.add_config_calculated_fields()

    assert list(builder.get_metadata().keys()) == ["concat_start_station_name_end_station_name"]


def test_column_validation_limit(module_under_test):
    mock_config_manager = ConfigManager(
        COLUMN_VALIDATION_CONFIG_LIMIT,
        MockIbisClient(),
        MockIbisClient(),
        verbose=False,
    )
    builder = module_under_test.ValidationBuilder(mock_config_manager)
    builder.add_query_limit()

    assert builder.source_builder.limit == QUERY_LIMIT


def test_validation_add_filters(module_under_test):
    mock_config_manager = ConfigManager(
        COLUMN_VALIDATION_CONFIG, MockIbisClient(), MockIbisClient(), verbose=False
    )
    builder = module_under_test.ValidationBuilder(mock_config_manager)

    builder.add_config_filters()
    filter_field = builder.source_builder.filters[0]

    assert filter_field.left == "column_name > 100"
