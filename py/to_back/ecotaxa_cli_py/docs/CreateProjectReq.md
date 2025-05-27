# CreateProjectReq

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**clone_of_id** | **int** | Internal, numeric id of a project to clone as a new one. By default it does not clone anything. | [optional] 
**title** | **str** | The project title, as text. | 
**instrument** | **str** | The project instrument. | [optional] [default to '?']
**access** | [**AccessLevelEnum**](AccessLevelEnum.md) | When \&quot;1\&quot; (PUBLIC), the project is created visible by all users.PUBLIC: \&quot;1\&quot;, OPEN: \&quot;2\&quot;, PRIVATE: \&quot;0\&quot; | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


