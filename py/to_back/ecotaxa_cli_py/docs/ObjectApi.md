# to_back.ecotaxa_cli_py.ObjectApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**object_query**](ObjectApi.md#object_query) | **GET** /object/{object_id} | Object Query
[**object_query_history**](ObjectApi.md#object_query_history) | **GET** /object/{object_id}/history | Object Query History


# **object_query**
> ObjectModel object_query(object_id)

Object Query

Returns **information about the object** corresponding to the given id.   🔒 Anonymous reader can do if the project has the right rights :)

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
    api_instance = to_back.ecotaxa_cli_py.ObjectApi(api_client)
    object_id = 1 # int | Internal, the unique numeric id of this object.

    try:
        # Object Query
        api_response = api_instance.object_query(object_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ObjectApi->object_query: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **object_id** | **int**| Internal, the unique numeric id of this object. | 

### Return type

[**ObjectModel**](ObjectModel.md)

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

# **object_query_history**
> list[HistoricalClassification] object_query_history(object_id)

Object Query History

Returns **information about the object's history** corresponding to the given id.

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
    api_instance = to_back.ecotaxa_cli_py.ObjectApi(api_client)
    object_id = 1 # int | Internal, the unique numeric id of this object.

    try:
        # Object Query History
        api_response = api_instance.object_query_history(object_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ObjectApi->object_query_history: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **object_id** | **int**| Internal, the unique numeric id of this object. | 

### Return type

[**list[HistoricalClassification]**](HistoricalClassification.md)

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

