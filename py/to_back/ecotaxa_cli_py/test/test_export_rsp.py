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
from to_back.ecotaxa_cli_py.models.export_rsp import ExportRsp  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestExportRsp(unittest.TestCase):
    """ExportRsp unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test ExportRsp
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.export_rsp.ExportRsp()  # noqa: E501
        if include_optional :
            return ExportRsp(
                errors = ["No content produced."," See previous warnings or check the presence of samples in the projects"], 
                warnings = ["No occurrence added for sample '3456' in 1"], 
                job_id = 12376
            )
        else :
            return ExportRsp(
        )

    def testExportRsp(self):
        """Test ExportRsp"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()