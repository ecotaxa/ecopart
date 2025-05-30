# to_back.ecotaxa_cli_py.AuthentificationApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**login**](AuthentificationApi.md#login) | **POST** /login | Login


# **login**
> str login(login_req)

Login

**Login barrier,**  If successful, the login will return a **JWT** which will have to be used in bearer authentication scheme for subsequent calls.

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
    api_instance = to_back.ecotaxa_cli_py.AuthentificationApi(api_client)
    login_req = to_back.ecotaxa_cli_py.LoginReq() # LoginReq | 

    try:
        # Login
        api_response = api_instance.login(login_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling AuthentificationApi->login: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **login_req** | [**LoginReq**](LoginReq.md)|  | 

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

