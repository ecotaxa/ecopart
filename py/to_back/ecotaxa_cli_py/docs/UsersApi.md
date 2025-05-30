# to_back.ecotaxa_cli_py.UsersApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**activate_user**](UsersApi.md#activate_user) | **POST** /users/activate/{user_id}/{status} | Activate User
[**create_user**](UsersApi.md#create_user) | **POST** /users/create | Create User
[**get_admin_users**](UsersApi.md#get_admin_users) | **GET** /users/user_admins | Get Admin Users
[**get_current_user_prefs**](UsersApi.md#get_current_user_prefs) | **GET** /users/my_preferences/{project_id} | Get Current User Prefs
[**get_user**](UsersApi.md#get_user) | **GET** /users/{user_id} | Get User
[**get_users**](UsersApi.md#get_users) | **GET** /users | Get Users
[**get_users_admins**](UsersApi.md#get_users_admins) | **GET** /users/admins | Get Users Admins
[**reset_user_password**](UsersApi.md#reset_user_password) | **POST** /users/reset_user_password | Reset User Password
[**search_user**](UsersApi.md#search_user) | **GET** /users/search | Search User
[**set_current_user_prefs**](UsersApi.md#set_current_user_prefs) | **PUT** /users/my_preferences/{project_id} | Set Current User Prefs
[**show_current_user**](UsersApi.md#show_current_user) | **GET** /users/me | Show Current User
[**update_user**](UsersApi.md#update_user) | **PUT** /users/{user_id} | Update User


# **activate_user**
> object activate_user(user_id, status, unknown_base_type, no_bot=no_bot)

Activate User

Activate a new user if external validation is on., return **NULL upon success.**  🔒 Depending on logged user, different authorizations apply: - An administrator or user administrator can activate a user or bypass the activation and inform the user when a modification request value/reason is provided. - An ordinary logged user cannot activate another account. If back-end configuration for self-creation check is Google reCAPTCHA, then no_bot is a pair [remote IP, reCAPTCHA response].

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    user_id = 1 # int | Internal, the unique numeric id of this user.
status = '1' # str | Internal, the status name assign to this user.
unknown_base_type = to_back.ecotaxa_cli_py.UNKNOWN_BASE_TYPE() # UNKNOWN_BASE_TYPE | 
no_bot = ['['127.0.0.1', 'ffqsdfsdf']'] # list[str] | not-a-robot proof (optional)

    try:
        # Activate User
        api_response = api_instance.activate_user(user_id, status, unknown_base_type, no_bot=no_bot)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->activate_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **int**| Internal, the unique numeric id of this user. | 
 **status** | **str**| Internal, the status name assign to this user. | 
 **unknown_base_type** | [**UNKNOWN_BASE_TYPE**](UNKNOWN_BASE_TYPE.md)|  | 
 **no_bot** | [**list[str]**](str.md)| not-a-robot proof | [optional] 

### Return type

**object**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_user**
> object create_user(user_model_with_rights, no_bot=no_bot, token=token)

Create User

**Create a new user**, return **NULL upon success.**  🔒 Depending on logged user, different authorizations apply: - An administrator or user administrator can create a user. - An unlogged user can self-create an account. But must eventually provide a no-robot proof. - An ordinary logged user cannot create another account.  If back-end configuration for self-creation check is Google reCAPTCHA, then no_bot is a pair [remote IP, reCAPTCHA response].

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    user_model_with_rights = to_back.ecotaxa_cli_py.UserModelWithRights() # UserModelWithRights | 
no_bot = ['['127.0.0.1', 'ffqsdfsdf']'] # list[str] | not-a-robot proof (optional)
token = 'token_example' # str | token in the url to validate request (optional)

    try:
        # Create User
        api_response = api_instance.create_user(user_model_with_rights, no_bot=no_bot, token=token)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->create_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_model_with_rights** | [**UserModelWithRights**](UserModelWithRights.md)|  | 
 **no_bot** | [**list[str]**](str.md)| not-a-robot proof | [optional] 
 **token** | **str**| token in the url to validate request | [optional] 

### Return type

**object**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_admin_users**
> list[MinUserModel] get_admin_users()

Get Admin Users

**List application administrators**, themselves being users. 🔒 Any authenticated user can access the list.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    
    try:
        # Get Admin Users
        api_response = api_instance.get_admin_users()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_admin_users: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[MinUserModel]**](MinUserModel.md)

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_current_user_prefs**
> str get_current_user_prefs(project_id, key)

Get Current User Prefs

**Returns one preference**, for a project and the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    project_id = 1 # int | Internal, numeric id of the project.
key = 'filters' # str | The preference key, as text.

    try:
        # Get Current User Prefs
        api_response = api_instance.get_current_user_prefs(project_id, key)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_current_user_prefs: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **int**| Internal, numeric id of the project. | 
 **key** | **str**| The preference key, as text. | 

### Return type

**str**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_user**
> MinUserModel get_user(user_id)

Get User

Returns **information about the user** corresponding to the given id.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    user_id = 1 # int | Internal, the unique numeric id of this user.

    try:
        # Get User
        api_response = api_instance.get_user(user_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **int**| Internal, the unique numeric id of this user. | 

### Return type

[**MinUserModel**](MinUserModel.md)

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_users**
> list[UserModelWithRights] get_users(ids=ids, fields=fields)

Get Users

Returns the list of **all users** with their full information, or just some of them if their ids are provided.  🔒 *For admins only.*

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    ids = '' # str | String containing the list of one or more id separated by non-num char.     **If several ids are provided**, one full info is returned per user. (optional) (default to '')
fields = '*default' # str | Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. (optional) (default to '*default')

    try:
        # Get Users
        api_response = api_instance.get_users(ids=ids, fields=fields)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_users: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ids** | **str**| String containing the list of one or more id separated by non-num char.     **If several ids are provided**, one full info is returned per user. | [optional] [default to &#39;&#39;]
 **fields** | **str**| Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. | [optional] [default to &#39;*default&#39;]

### Return type

[**list[UserModelWithRights]**](UserModelWithRights.md)

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_users_admins**
> list[MinUserModel] get_users_admins()

Get Users Admins

**List users administrators**, themselves being users. 🔒 Public, no auth.

### Example

```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)


# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    
    try:
        # Get Users Admins
        api_response = api_instance.get_users_admins()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_users_admins: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[MinUserModel]**](MinUserModel.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reset_user_password**
> object reset_user_password(reset_password_req, no_bot=no_bot, token=token)

Reset User Password

reset user password **return NULL on success**  🔒 Depending on logged user, different authorizations apply: - An administrator or user administrator can reset a user password. - An unlogged user can ask for a reset  in two steps. and receive a mail with a token. But must eventually provide a no-robot proof.  If back-end configuration for self-creation check is Google reCAPTCHA, then no_bot is a pair [remote IP, reCAPTCHA response].

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    reset_password_req = to_back.ecotaxa_cli_py.ResetPasswordReq() # ResetPasswordReq | 
no_bot = ['['127.0.0.1', 'ffqsdfsdf']'] # list[str] | not-a-robot proof (optional)
token = 'token_example' # str | token in the url to validate request (optional)

    try:
        # Reset User Password
        api_response = api_instance.reset_user_password(reset_password_req, no_bot=no_bot, token=token)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->reset_user_password: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **reset_password_req** | [**ResetPasswordReq**](ResetPasswordReq.md)|  | 
 **no_bot** | [**list[str]**](str.md)| not-a-robot proof | [optional] 
 **token** | **str**| token in the url to validate request | [optional] 

### Return type

**object**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_user**
> list[MinUserModel] search_user(by_name=by_name)

Search User

**Search users using various criteria**, search is case-insensitive and might contain % chars.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    by_name = '%userNa%' # str | Search by name, use % for searching with 'any char'. (optional)

    try:
        # Search User
        api_response = api_instance.search_user(by_name=by_name)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->search_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **by_name** | **str**| Search by name, use % for searching with &#39;any char&#39;. | [optional] 

### Return type

[**list[MinUserModel]**](MinUserModel.md)

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_current_user_prefs**
> object set_current_user_prefs(project_id, key, value)

Set Current User Prefs

**Sets one preference**, for a project and for the currently authenticated user.  Available keys are **cwd**, **img_import** and **filters**.  The key disappears if set to empty string.  **Returns NULL upon success.**

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    project_id = 1 # int | Internal, numeric id of the project.
key = 'filters' # str | The preference key, as text.
value = '{\"dispfield\": \" dispfield_orig_id dispfield_classif_auto_score dispfield_classif_when dispfield_random_value\", \"ipp\": \"500\", \"magenabled\": \"1\", \"popupenabled\": \"1\", \"sortby\": \"orig_id\", \"sortorder\": \"asc\", \"statusfilter\": \"\", \"zoom\": \"90\"}' # str | The value to set this preference to, as text.

    try:
        # Set Current User Prefs
        api_response = api_instance.set_current_user_prefs(project_id, key, value)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->set_current_user_prefs: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_id** | **int**| Internal, numeric id of the project. | 
 **key** | **str**| The preference key, as text. | 
 **value** | **str**| The value to set this preference to, as text. | 

### Return type

**object**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **show_current_user**
> UserModelWithRights show_current_user()

Show Current User

Returns **currently authenticated user's** (i.e. you) information, permissions and last used projects.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    
    try:
        # Show Current User
        api_response = api_instance.show_current_user()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->show_current_user: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserModelWithRights**](UserModelWithRights.md)

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_user**
> object update_user(user_id, user_model_with_rights)

Update User

**Update the user**, return **NULL upon success.**  🔒 Depending on logged user, different authorizations apply: - An administrator or user administrator can change any field with respect of consistency. - A user can update own password and name. - An ordinary user cannot update anything for another user.

### Example

* OAuth Authentication (BearerOrCookieAuth):
```python
from __future__ import print_function
import time
import to_back.ecotaxa_cli_py
from to_back.ecotaxa_cli_py.rest import ApiException
from pprint import pprint
# Defining the host is optional and defaults to https://raw.githubusercontent.com/api
# See configuration.py for a list of all supported configuration parameters.
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure OAuth2 access token for authorization: BearerOrCookieAuth
configuration = to_back.ecotaxa_cli_py.Configuration(
    host = "https://raw.githubusercontent.com/api"
)
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# Enter a context with an instance of the API client
with to_back.ecotaxa_cli_py.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = to_back.ecotaxa_cli_py.UsersApi(api_client)
    user_id = 760 # int | Internal, numeric id of the user.
user_model_with_rights = to_back.ecotaxa_cli_py.UserModelWithRights() # UserModelWithRights | 

    try:
        # Update User
        api_response = api_instance.update_user(user_id, user_model_with_rights)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->update_user: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **user_id** | **int**| Internal, numeric id of the user. | 
 **user_model_with_rights** | [**UserModelWithRights**](UserModelWithRights.md)|  | 

### Return type

**object**

### Authorization

[BearerOrCookieAuth](../README.md#BearerOrCookieAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

