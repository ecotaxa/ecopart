# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.25
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest

import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.api.samples_api import SamplesApi  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException


class TestSamplesApi(unittest.TestCase):
    """SamplesApi unit test stubs"""

    def setUp(self):
        self.api = to_back.ecotaxa_cli_py.api.samples_api.SamplesApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_sample_query(self):
        """Test case for sample_query

        Sample Query  # noqa: E501
        """
        pass

    def test_sample_set_get_stats(self):
        """Test case for sample_set_get_stats

        Sample Set Get Stats  # noqa: E501
        """
        pass

    def test_samples_search(self):
        """Test case for samples_search

        Samples Search  # noqa: E501
        """
        pass

    def test_update_samples(self):
        """Test case for update_samples

        Update Samples  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()