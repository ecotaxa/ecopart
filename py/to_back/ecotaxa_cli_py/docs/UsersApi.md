# to_back.ecotaxa_cli_py.UsersApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_current_user_prefs**](UsersApi.md#get_current_user_prefs) | **GET** /users/my_preferences/{project_id} | Get Current User Prefs
[**get_user**](UsersApi.md#get_user) | **GET** /users/{user_id} | Get User
[**get_users**](UsersApi.md#get_users) | **GET** /users | Get Users
[**get_users_admins**](UsersApi.md#get_users_admins) | **GET** /users/admins | Get Users Admins
[**search_user**](UsersApi.md#search_user) | **GET** /users/search | Search User
[**set_current_user_prefs**](UsersApi.md#set_current_user_prefs) | **PUT** /users/my_preferences/{project_id} | Set Current User Prefs
[**show_current_user**](UsersApi.md#show_current_user) | **GET** /users/me | Show Current User


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
> UserModel get_user(user_id)

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

[**UserModel**](UserModel.md)

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
> list[UserModel] get_users()

Get Users

Returns the list of **all users** with their information.   🔒 *For admins only.*

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
        # Get Users
        api_response = api_instance.get_users()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_users: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[UserModel]**](UserModel.md)

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

# **get_users_admins**
> list[UserModel] get_users_admins()

Get Users Admins

**List users administrators**, themselves being users.

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
        # Get Users Admins
        api_response = api_instance.get_users_admins()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UsersApi->get_users_admins: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[UserModel]**](UserModel.md)

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

# **search_user**
> list[UserModel] search_user(by_name=by_name)

Search User

**Search users using various criteria**, search is case insensitive and might contain % chars.

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

[**list[UserModel]**](UserModel.md)

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
