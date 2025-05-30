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
from to_back.ecotaxa_cli_py.models.body_predict_object_set_object_set_predict_post import BodyPredictObjectSetObjectSetPredictPost  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestBodyPredictObjectSetObjectSetPredictPost(unittest.TestCase):
    """BodyPredictObjectSetObjectSetPredictPost unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test BodyPredictObjectSetObjectSetPredictPost
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.body_predict_object_set_object_set_predict_post.BodyPredictObjectSetObjectSetPredictPost()  # noqa: E501
        if include_optional :
            return BodyPredictObjectSetObjectSetPredictPost(
                filters = to_back.ecotaxa_cli_py.models.project_filters_model.Project filters Model(
                    taxo = '12,7654,5409', 
                    taxochild = 'Y', 
                    statusfilter = 'NV', 
                    map_n = '44.34', 
                    map_w = '3.88', 
                    map_e = '7.94', 
                    map_s = '42.42', 
                    depthmin = '10', 
                    depthmax = '110', 
                    samples = '10987,3456,987,38', 
                    instrum = 'uvp5', 
                    daytime = 'N,A', 
                    month = '11,12', 
                    fromdate = '2020-10-09', 
                    todate = '2021-10-09', 
                    fromtime = '1:17:00', 
                    totime = '23:32:00', 
                    inverttime = '0', 
                    validfromdate = '2020-10-09 10:00:00', 
                    validtodate = '2021-10-09 10:00:00', 
                    freenum = 'n01', 
                    freenumst = '0', 
                    freenumend = '999999', 
                    freetxt = 'p01', 
                    freetxtval = 'zooprocess', 
                    filt_annot = '34,67,67', 
                    filt_last_annot = '34,67', ), 
                request = {"project_id":[3426],"source_project_ids":[1040,1820],"features":["fre.area","fre.esd","obj.depth_max"],"use_scn":true}
            )
        else :
            return BodyPredictObjectSetObjectSetPredictPost(
                filters = to_back.ecotaxa_cli_py.models.project_filters_model.Project filters Model(
                    taxo = '12,7654,5409', 
                    taxochild = 'Y', 
                    statusfilter = 'NV', 
                    map_n = '44.34', 
                    map_w = '3.88', 
                    map_e = '7.94', 
                    map_s = '42.42', 
                    depthmin = '10', 
                    depthmax = '110', 
                    samples = '10987,3456,987,38', 
                    instrum = 'uvp5', 
                    daytime = 'N,A', 
                    month = '11,12', 
                    fromdate = '2020-10-09', 
                    todate = '2021-10-09', 
                    fromtime = '1:17:00', 
                    totime = '23:32:00', 
                    inverttime = '0', 
                    validfromdate = '2020-10-09 10:00:00', 
                    validtodate = '2021-10-09 10:00:00', 
                    freenum = 'n01', 
                    freenumst = '0', 
                    freenumend = '999999', 
                    freetxt = 'p01', 
                    freetxtval = 'zooprocess', 
                    filt_annot = '34,67,67', 
                    filt_last_annot = '34,67', ),
                request = {"project_id":[3426],"source_project_ids":[1040,1820],"features":["fre.area","fre.esd","obj.depth_max"],"use_scn":true},
        )

    def testBodyPredictObjectSetObjectSetPredictPost(self):
        """Test BodyPredictObjectSetObjectSetPredictPost"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
