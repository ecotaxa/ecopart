# to_back.ecotaxa_cli_py.CollectionsApi

All URIs are relative to *https://raw.githubusercontent.com/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**collection_aggregated_projects_properties**](CollectionsApi.md#collection_aggregated_projects_properties) | **GET** /collections/aggregated_projects_properties | Collection Aggregated Projects Properties
[**collection_by_short_title**](CollectionsApi.md#collection_by_short_title) | **GET** /collections/by_short_title | Collection By Short Title
[**collection_by_title**](CollectionsApi.md#collection_by_title) | **GET** /collections/by_title | Collection By Title
[**create_collection**](CollectionsApi.md#create_collection) | **POST** /collections/create | Create Collection
[**darwin_core_format_export**](CollectionsApi.md#darwin_core_format_export) | **POST** /collections/export/darwin_core | Darwin Core Format Export
[**erase_collection**](CollectionsApi.md#erase_collection) | **DELETE** /collections/{collection_id} | Erase Collection
[**get_collection**](CollectionsApi.md#get_collection) | **GET** /collections/{collection_id} | Get Collection
[**get_collection_taxonomy_recast**](CollectionsApi.md#get_collection_taxonomy_recast) | **GET** /collections/{collection_id}/taxo_recast | Read Collection Taxo Recast
[**list_collections**](CollectionsApi.md#list_collections) | **GET** /collections | List Collections
[**patch_collection**](CollectionsApi.md#patch_collection) | **PATCH** /collections/{collection_id} | Patch Collection
[**search_collections**](CollectionsApi.md#search_collections) | **GET** /collections/search | Search Collections
[**update_collection**](CollectionsApi.md#update_collection) | **PUT** /collections/{collection_id} | Update Collection
[**update_collection_taxonomy_recast**](CollectionsApi.md#update_collection_taxonomy_recast) | **PUT** /collections/{collection_id}/taxo_recast | Update Collection Taxo Recast


# **collection_aggregated_projects_properties**
> CollectionAggregatedRsp collection_aggregated_projects_properties(project_ids)

Collection Aggregated Projects Properties

**returns projectset calculated selected fields values  projects and list of rejected projects id. Note: 'manage' right is required on all underlying projects.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    project_ids = '1' # str | String containing the list of one or more project id separated by non-num char.   .

    try:
        # Collection Aggregated Projects Properties
        api_response = api_instance.collection_aggregated_projects_properties(project_ids)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->collection_aggregated_projects_properties: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **project_ids** | **str**| String containing the list of one or more project id separated by non-num char.   . | 

### Return type

[**CollectionAggregatedRsp**](CollectionAggregatedRsp.md)

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

# **collection_by_short_title**
> CollectionModel collection_by_short_title(q)

Collection By Short Title

Return the **single collection with this short title**.  *For published datasets.*  ⚠️ DO NOT MODIFY BEHAVIOR ⚠️

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    q = 'My coll' # str | Search by **exact** short title.

    try:
        # Collection By Short Title
        api_response = api_instance.collection_by_short_title(q)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->collection_by_short_title: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**| Search by **exact** short title. | 

### Return type

[**CollectionModel**](CollectionModel.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **collection_by_title**
> CollectionModel collection_by_title(q)

Collection By Title

Return the **single collection with this title**.  *For published datasets.*  ⚠️ DO NOT MODIFY BEHAVIOR ⚠️

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    q = 'My collection' # str | Search by **exact** title.

    try:
        # Collection By Title
        api_response = api_instance.collection_by_title(q)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->collection_by_title: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**| Search by **exact** title. | 

### Return type

[**CollectionModel**](CollectionModel.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_collection**
> int create_collection(create_collection_req)

Create Collection

**Create a collection** with at least one project inside.  Returns the created collection Id.  Note: 'manage' right is required on all underlying projects.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    create_collection_req = to_back.ecotaxa_cli_py.CreateCollectionReq() # CreateCollectionReq | 

    try:
        # Create Collection
        api_response = api_instance.create_collection(create_collection_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->create_collection: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_collection_req** | [**CreateCollectionReq**](CreateCollectionReq.md)|  | 

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

# **darwin_core_format_export**
> ExportRsp darwin_core_format_export(darwin_core_export_req)

Darwin Core Format Export

**Export the collection in Darwin Core format, e.g. for EMODnet portal**, @see https://www.emodnet-ingestion.eu  Produces a DwC-A (https://dwc.tdwg.org/) archive into a temporary directory, ready for download.  Maybe useful, a reader in Python: https://python-dwca-reader.readthedocs.io/en/latest/index.html  Note: Only manageable collections can be exported.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    darwin_core_export_req = to_back.ecotaxa_cli_py.DarwinCoreExportReq() # DarwinCoreExportReq | 

    try:
        # Darwin Core Format Export
        api_response = api_instance.darwin_core_format_export(darwin_core_export_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->darwin_core_format_export: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **darwin_core_export_req** | [**DarwinCoreExportReq**](DarwinCoreExportReq.md)|  | 

### Return type

[**ExportRsp**](ExportRsp.md)

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

# **erase_collection**
> int erase_collection(collection_id)

Erase Collection

**Delete the collection**,  i.e. the precious fields, as the projects are just linked-at from the collection.  Note: Only manageable collections can be deleted.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.

    try:
        # Erase Collection
        api_response = api_instance.erase_collection(collection_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->erase_collection: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 

### Return type

**int**

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

# **get_collection**
> CollectionModel get_collection(collection_id)

Get Collection

Returns **information about the collection** corresponding to the given id.  Note: The collection is returned only if manageable.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.

    try:
        # Get Collection
        api_response = api_instance.get_collection(collection_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->get_collection: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 

### Return type

[**CollectionModel**](CollectionModel.md)

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

# **get_collection_taxonomy_recast**
> object get_collection_taxonomy_recast(collection_id)

Read Collection Taxo Recast

**Read the collection taxonomy recast**.   **Returns NULL upon success.**   Note: The collection data is returned only if manageable.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.

    try:
        # Read Collection Taxo Recast
        api_response = api_instance.get_collection_taxonomy_recast(collection_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->get_collection_taxonomy_recast: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 

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

# **list_collections**
> list[CollectionModel] list_collections(collection_ids=collection_ids, fields=fields)

List Collections

**Search for collections.**  Note: Only collections where the current user is manager are returned. All collections are returned if the user is application administrator

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_ids = '123,45' # str | limit the list to a set of ids. (optional)
fields = '*default' # str | Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. (optional) (default to '*default')

    try:
        # List Collections
        api_response = api_instance.list_collections(collection_ids=collection_ids, fields=fields)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->list_collections: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_ids** | **str**| limit the list to a set of ids. | [optional] 
 **fields** | **str**| Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. | [optional] [default to &#39;*default&#39;]

### Return type

[**list[CollectionModel]**](CollectionModel.md)

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

# **patch_collection**
> object patch_collection(collection_id, collection_req)

Patch Collection

**Partial Update of the collection**. Note that some updates are silently failing when not compatible  with the composing projects.   **Returns NULL upon success.**   Note: The collection is partiallly updated only if manageable.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.
collection_req = to_back.ecotaxa_cli_py.CollectionReq() # CollectionReq | 

    try:
        # Patch Collection
        api_response = api_instance.patch_collection(collection_id, collection_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->patch_collection: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 
 **collection_req** | [**CollectionReq**](CollectionReq.md)|  | 

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

# **search_collections**
> list[CollectionModel] search_collections(title, fields=fields)

Search Collections

**Search for collections.**  Note: Only manageable collections are returned.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    title = '%coll%' # str | Search by title, use % for searching with 'any char'.
fields = '*default' # str | Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. (optional) (default to '*default')

    try:
        # Search Collections
        api_response = api_instance.search_collections(title, fields=fields)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->search_collections: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **title** | **str**| Search by title, use % for searching with &#39;any char&#39;. | 
 **fields** | **str**| Return the default fields (typically used in conjunction with an additional field list). For users list display purpose. | [optional] [default to &#39;*default&#39;]

### Return type

[**list[CollectionModel]**](CollectionModel.md)

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

# **update_collection**
> object update_collection(collection_id, collection_req)

Update Collection

**Update the collection**. Note that some updates are silently failing when not compatible  with the composing projects.   **Returns NULL upon success.**   Note: The collection is updated only if manageable.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.
collection_req = to_back.ecotaxa_cli_py.CollectionReq() # CollectionReq | 

    try:
        # Update Collection
        api_response = api_instance.update_collection(collection_id, collection_req)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->update_collection: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 
 **collection_req** | [**CollectionReq**](CollectionReq.md)|  | 

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

# **update_collection_taxonomy_recast**
> object update_collection_taxonomy_recast(collection_id, taxonomy_recast)

Update Collection Taxo Recast

**Create or Update the collection taxonomy recast**.   **Returns NULL upon success.**   Note: The collection is updated only if manageable.

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
    api_instance = to_back.ecotaxa_cli_py.CollectionsApi(api_client)
    collection_id = 1 # int | Internal, the unique numeric id of this collection.
taxonomy_recast = to_back.ecotaxa_cli_py.TaxonomyRecast() # TaxonomyRecast | 

    try:
        # Update Collection Taxo Recast
        api_response = api_instance.update_collection_taxonomy_recast(collection_id, taxonomy_recast)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling CollectionsApi->update_collection_taxonomy_recast: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **collection_id** | **int**| Internal, the unique numeric id of this collection. | 
 **taxonomy_recast** | [**TaxonomyRecast**](TaxonomyRecast.md)|  | 

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

