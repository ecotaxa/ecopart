# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.25
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest
import datetime

import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.models.sample_taxo_stats_model import SampleTaxoStatsModel  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestSampleTaxoStatsModel(unittest.TestCase):
    """SampleTaxoStatsModel unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test SampleTaxoStatsModel
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.sample_taxo_stats_model.SampleTaxoStatsModel()  # noqa: E501
        if include_optional :
            return SampleTaxoStatsModel(
                sample_id = 56, 
                used_taxa = [
                    56
                    ], 
                nb_unclassified = 56, 
                nb_validated = 56, 
                nb_dubious = 56, 
                nb_predicted = 56
            )
        else :
            return SampleTaxoStatsModel(
        )

    def testSampleTaxoStatsModel(self):
        """Test SampleTaxoStatsModel"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()