# coding: utf-8

"""
    EcoTaxa

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    The version of the OpenAPI document: 0.0.25
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from to_back.ecotaxa_cli_py.api_client import ApiClient
from to_back.ecotaxa_cli_py.exceptions import (  # noqa: F401
    ApiTypeError,
    ApiValueError
)


class UsersApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def get_current_user_prefs(self, project_id, key, **kwargs):  # noqa: E501
        """Get Current User Prefs  # noqa: E501

        **Returns one preference**, for a project and the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_current_user_prefs(project_id, key, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int project_id: Internal, numeric id of the project. (required)
        :param str key: The preference key, as text. (required)
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.get_current_user_prefs_with_http_info(project_id, key, **kwargs)  # noqa: E501

    def get_current_user_prefs_with_http_info(self, project_id, key, **kwargs):  # noqa: E501
        """Get Current User Prefs  # noqa: E501

        **Returns one preference**, for a project and the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_current_user_prefs_with_http_info(project_id, key, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int project_id: Internal, numeric id of the project. (required)
        :param str key: The preference key, as text. (required)
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(str, status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
            'project_id',
            'key'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_current_user_prefs" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'project_id' is set
        if self.api_client.client_side_validation and ('project_id' not in local_var_params or  # noqa: E501
                                                        local_var_params['project_id'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `project_id` when calling `get_current_user_prefs`")  # noqa: E501
        # verify the required parameter 'key' is set
        if self.api_client.client_side_validation and ('key' not in local_var_params or  # noqa: E501
                                                        local_var_params['key'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `key` when calling `get_current_user_prefs`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'project_id' in local_var_params:
            path_params['project_id'] = local_var_params['project_id']  # noqa: E501

        query_params = []
        if 'key' in local_var_params and local_var_params['key'] is not None:  # noqa: E501
            query_params.append(('key', local_var_params['key']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/my_preferences/{project_id}', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='str',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_user(self, user_id, **kwargs):  # noqa: E501
        """Get User  # noqa: E501

        Returns **information about the user** corresponding to the given id.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_user(user_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int user_id: Internal, the unique numeric id of this user. (required)
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: UserModel
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.get_user_with_http_info(user_id, **kwargs)  # noqa: E501

    def get_user_with_http_info(self, user_id, **kwargs):  # noqa: E501
        """Get User  # noqa: E501

        Returns **information about the user** corresponding to the given id.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_user_with_http_info(user_id, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int user_id: Internal, the unique numeric id of this user. (required)
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(UserModel, status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
            'user_id'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_user" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'user_id' is set
        if self.api_client.client_side_validation and ('user_id' not in local_var_params or  # noqa: E501
                                                        local_var_params['user_id'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `user_id` when calling `get_user`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'user_id' in local_var_params:
            path_params['user_id'] = local_var_params['user_id']  # noqa: E501

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/{user_id}', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='UserModel',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_users(self, **kwargs):  # noqa: E501
        """Get Users  # noqa: E501

        Returns the list of **all users** with their information.   🔒 *For admins only.*  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_users(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: list[UserModel]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.get_users_with_http_info(**kwargs)  # noqa: E501

    def get_users_with_http_info(self, **kwargs):  # noqa: E501
        """Get Users  # noqa: E501

        Returns the list of **all users** with their information.   🔒 *For admins only.*  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_users_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(list[UserModel], status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_users" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[UserModel]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_users_admins(self, **kwargs):  # noqa: E501
        """Get Users Admins  # noqa: E501

        **List users administrators**, themselves being users.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_users_admins(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: list[UserModel]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.get_users_admins_with_http_info(**kwargs)  # noqa: E501

    def get_users_admins_with_http_info(self, **kwargs):  # noqa: E501
        """Get Users Admins  # noqa: E501

        **List users administrators**, themselves being users.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_users_admins_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(list[UserModel], status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_users_admins" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/admins', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[UserModel]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def search_user(self, **kwargs):  # noqa: E501
        """Search User  # noqa: E501

        **Search users using various criteria**, search is case insensitive and might contain % chars.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.search_user(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param str by_name: Search by name, use % for searching with 'any char'.
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: list[UserModel]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.search_user_with_http_info(**kwargs)  # noqa: E501

    def search_user_with_http_info(self, **kwargs):  # noqa: E501
        """Search User  # noqa: E501

        **Search users using various criteria**, search is case insensitive and might contain % chars.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.search_user_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param str by_name: Search by name, use % for searching with 'any char'.
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(list[UserModel], status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
            'by_name'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method search_user" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []
        if 'by_name' in local_var_params and local_var_params['by_name'] is not None:  # noqa: E501
            query_params.append(('by_name', local_var_params['by_name']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/search', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[UserModel]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def set_current_user_prefs(self, project_id, key, value, **kwargs):  # noqa: E501
        """Set Current User Prefs  # noqa: E501

        **Sets one preference**, for a project and for the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.  The key disappears if set to empty string.  **Returns NULL upon success.**  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.set_current_user_prefs(project_id, key, value, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int project_id: Internal, numeric id of the project. (required)
        :param str key: The preference key, as text. (required)
        :param str value: The value to set this preference to, as text. (required)
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: object
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.set_current_user_prefs_with_http_info(project_id, key, value, **kwargs)  # noqa: E501

    def set_current_user_prefs_with_http_info(self, project_id, key, value, **kwargs):  # noqa: E501
        """Set Current User Prefs  # noqa: E501

        **Sets one preference**, for a project and for the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.  The key disappears if set to empty string.  **Returns NULL upon success.**  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.set_current_user_prefs_with_http_info(project_id, key, value, async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param int project_id: Internal, numeric id of the project. (required)
        :param str key: The preference key, as text. (required)
        :param str value: The value to set this preference to, as text. (required)
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(object, status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
            'project_id',
            'key',
            'value'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method set_current_user_prefs" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'project_id' is set
        if self.api_client.client_side_validation and ('project_id' not in local_var_params or  # noqa: E501
                                                        local_var_params['project_id'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `project_id` when calling `set_current_user_prefs`")  # noqa: E501
        # verify the required parameter 'key' is set
        if self.api_client.client_side_validation and ('key' not in local_var_params or  # noqa: E501
                                                        local_var_params['key'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `key` when calling `set_current_user_prefs`")  # noqa: E501
        # verify the required parameter 'value' is set
        if self.api_client.client_side_validation and ('value' not in local_var_params or  # noqa: E501
                                                        local_var_params['value'] is None):  # noqa: E501
            raise ApiValueError("Missing the required parameter `value` when calling `set_current_user_prefs`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'project_id' in local_var_params:
            path_params['project_id'] = local_var_params['project_id']  # noqa: E501

        query_params = []
        if 'key' in local_var_params and local_var_params['key'] is not None:  # noqa: E501
            query_params.append(('key', local_var_params['key']))  # noqa: E501
        if 'value' in local_var_params and local_var_params['value'] is not None:  # noqa: E501
            query_params.append(('value', local_var_params['value']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/my_preferences/{project_id}', 'PUT',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='object',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)

    def show_current_user(self, **kwargs):  # noqa: E501
        """Show Current User  # noqa: E501

        Returns **currently authenticated user's** (i.e. you) information, permissions and last used projects.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.show_current_user(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: UserModelWithRights
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        return self.show_current_user_with_http_info(**kwargs)  # noqa: E501

    def show_current_user_with_http_info(self, **kwargs):  # noqa: E501
        """Show Current User  # noqa: E501

        Returns **currently authenticated user's** (i.e. you) information, permissions and last used projects.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.show_current_user_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool: execute request asynchronously
        :param _return_http_data_only: response data without head status code
                                       and headers
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: tuple(UserModelWithRights, status_code(int), headers(HTTPHeaderDict))
                 If the method is called asynchronously,
                 returns the request thread.
        """

        local_var_params = locals()

        all_params = [
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method show_current_user" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BearerOrCookieAuth']  # noqa: E501

        return self.api_client.call_api(
            '/users/me', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='UserModelWithRights',  # noqa: E501
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats)