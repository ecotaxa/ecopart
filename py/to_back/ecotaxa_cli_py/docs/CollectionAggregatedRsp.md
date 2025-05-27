# CollectionAggregatedRsp

collection model extended with computed information about the collection projects
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**can_be_administered** | **bool** | Whether the current user is manager of all collection projects | [optional] [default to False]
**instrument** | **str** | The collection instrument from projects. | [optional] [default to '?']
**access** | [**AccessLevelEnum**](AccessLevelEnum.md) | The restricted access for collection projects.PUBLIC: \&quot;1\&quot;, OPEN: \&quot;2\&quot;, PRIVATE: \&quot;0\&quot; | [optional] 
**initclassiflist** | **str** |  Aggregated categories from the collection projects. | 
**classiffieldlist** | **str** |  Aggregated sorting and displaying fields from the collection projects. | 
**cnn_network_id** | **str** |  Common deep features for the collection projects. Can be None (???) | 
**status** | **str** |  the restricted collection status calculated from projects. | 
**creator_users** | [**list[MinUserModel]**](MinUserModel.md) | Annotators extracted from history. | [optional] [default to []]
**privileges** | **dict(str, list[MinUserModel])** | Aggregated user privileges of projects with user minimal right on projects | [optional] 
**freecols** | **dict(str, dict(str, str))** | Common free cols of projects. | [optional] 
**excluded** | **dict(str, list[int])** | Excluded projects for common values  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


