# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.41
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest

import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.api.admin_api import AdminApi  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException


class TestAdminApi(unittest.TestCase):
    """AdminApi unit test stubs"""

    def setUp(self):
        self.api = to_back.ecotaxa_cli_py.api.admin_api.AdminApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_db_direct_query(self):
        """Test case for db_direct_query

        Direct Db Query  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()
