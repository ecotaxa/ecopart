# to_back.ecotaxa_cli_py.ProcessesApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**process_query**](ProcessesApi.md#process_query) | **GET** /process/{process_id} | Process Query
[**update_processes**](ProcessesApi.md#update_processes) | **POST** /process_set/update | Update Processes


# **process_query**
> ProcessModel process_query(process_id)

Process Query

Returns **information about the process** corresponding to the given id.

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
    api_instance = to_back.ecotaxa_cli_py.ProcessesApi(api_client)
    process_id = 1 # int | Internal, the unique numeric id of this process.

    try:
        # Process Query
        api_response = api_instance.process_query(process_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProcessesApi->process_query: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **process_id** | **int**| Internal, the unique numeric id of this process. | 

### Return type

[**ProcessModel**](ProcessModel.md)

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

# **update_processes**
> int update_processes(bulk_update_req)

Update Processes

Do the required **update for each process in the set.**  **Returns the number of updated entities.**

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
    api_instance = to_back.ecotaxa_cli_py.ProcessesApi(api_client)
    bulk_update_req = to_back.ecotaxa_cli_py.BulkUpdateReq() # BulkUpdateReq | 

    try:
        # Update Processes
        api_response = api_instance.update_processes(bulk_update_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProcessesApi->update_processes: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bulk_update_req** | [**BulkUpdateReq**](BulkUpdateReq.md)|  | 

### Return type

**int**

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

