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
from to_back.ecotaxa_cli_py.models.body_put_user_file_my_files_post import BodyPutUserFileMyFilesPost  # noqa: E501
from to_back.ecotaxa_cli_py.rest import ApiException

class TestBodyPutUserFileMyFilesPost(unittest.TestCase):
    """BodyPutUserFileMyFilesPost unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test BodyPutUserFileMyFilesPost
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = to_back.ecotaxa_cli_py.models.body_put_user_file_my_files_post.BodyPutUserFileMyFilesPost()  # noqa: E501
        if include_optional :
            return BodyPutUserFileMyFilesPost(
                file = bytes(b'blah'), 
                path = '0', 
                tag = '0'
            )
        else :
            return BodyPutUserFileMyFilesPost(
                file = bytes(b'blah'),
        )

    def testBodyPutUserFileMyFilesPost(self):
        """Test BodyPutUserFileMyFilesPost"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
