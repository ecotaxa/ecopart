# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.41
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest
import datetime

import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.models.historical_last_classif import HistoricalLastClassif  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestHistoricalLastClassif(unittest.TestCase):
    """HistoricalLastClassif unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test HistoricalLastClassif
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.historical_last_classif.HistoricalLastClassif()  # noqa: E501
        if include_optional :
            return HistoricalLastClassif(
                objid = 264409236, 
                classif_id = 82399, 
                histo_classif_date = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), 
                histo_classif_id = 56, 
                histo_classif_type = 'M', 
                histo_classif_qual = 'V', 
                histo_classif_who = 3876, 
                histo_classif_score = 1.337
            )
        else :
            return HistoricalLastClassif(
        )

    def testHistoricalLastClassif(self):
        """Test HistoricalLastClassif"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
