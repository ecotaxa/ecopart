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
from to_back.ecotaxa_cli_py.models.object_model import ObjectModel  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestObjectModel(unittest.TestCase):
    """ObjectModel unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test ObjectModel
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.object_model.ObjectModel()  # noqa: E501
        if include_optional :
            return ObjectModel(
                classif_when = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), 
                classif_auto_id = 56, 
                classif_auto_score = 0.085, 
                classif_auto_when = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), 
                objid = 264409236, 
                acquisid = 144, 
                classif_id = 82399, 
                objtime = '0', 
                latitude = 42.0231666666667, 
                longitude = 4.71766666666667, 
                depth_min = 0, 
                depth_max = 300, 
                objdate = datetime.datetime.strptime('1975-12-30', '%Y-%m-%d').date(), 
                classif_qual = 'P', 
                sunpos = 'N', 
                classif_score = 1.337, 
                classif_who = 56, 
                orig_id = 'deex_leg1_48_406', 
                object_link = 'http://www.zooscan.obs-vlfr.fr//', 
                complement_info = 'Part of ostracoda', 
                sample_id = 12, 
                project_id = 76, 
                images = [{"imgid":376456,"objid":376456,"imgrank":0,"file_name":"0037/6456.jpg","orig_file_name":"dewex_leg2_63_689.jpg","width":98,"height":63,"thumb_file_name":"null","thumb_width":"null","thumb_height":"null"}], 
                free_columns = {"area":49.0,"mean":232.27,"stddev":2.129}, 
                classif_crossvalidation_id = 56, 
                similarity = 1.337, 
                random_value = 1234
            )
        else :
            return ObjectModel(
                objid = 264409236,
                acquisid = 144,
                orig_id = 'deex_leg1_48_406',
                sample_id = 12,
                project_id = 76,
                random_value = 1234,
        )

    def testObjectModel(self):
        """Test ObjectModel"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
