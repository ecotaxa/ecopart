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
from to_back.ecotaxa_cli_py.models.taxon_model import TaxonModel  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestTaxonModel(unittest.TestCase):
    """TaxonModel unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test TaxonModel
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.taxon_model.TaxonModel()  # noqa: E501
        if include_optional :
            return TaxonModel(
                id = 1, 
                renm_id = 56, 
                name = 'living', 
                type = 'P', 
                nb_objects = 34118, 
                nb_children_objects = 30091727, 
                display_name = 'living<', 
                lineage = ["living"], 
                id_lineage = [1], 
                children = [92952,2,92329,85048,4,93599,93687,85011,92951,93698,84961,92696,3]
            )
        else :
            return TaxonModel(
                id = 1,
                name = 'living',
                type = 'P',
                nb_objects = 34118,
                nb_children_objects = 30091727,
                display_name = 'living<',
                lineage = ["living"],
                id_lineage = [1],
                children = [92952,2,92329,85048,4,93599,93687,85011,92951,93698,84961,92696,3],
        )

    def testTaxonModel(self):
        """Test TaxonModel"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()