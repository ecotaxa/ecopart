# CollectionModel

Basic and computed information about the Collection.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | The collection Id. | 
**external_id** | **str** | The external Id. | 
**external_id_system** | **str** | The external Id system. | 
**title** | **str** | The collection title. | 
**short_title** | **str** | The collection short title. | [optional] 
**citation** | **str** | The collection citation. | [optional] 
**license** | **str** | The collection license. | [optional] 
**abstract** | **str** | The collection abstract. | [optional] 
**description** | **str** | The collection description. | [optional] 
**project_ids** | **list[int]** | The list of composing project IDs. | 
**provider_user** | [**MinUserModel**](MinUserModel.md) | Is the person who         is responsible for the content of this metadata record. Writer of the title and abstract. | [optional] 
**contact_user** | [**MinUserModel**](MinUserModel.md) | Is the person who         should be contacted in cases of questions regarding the content of the dataset or any data restrictions.         This is also the person who is most likely to stay involved in the dataset the longest. | [optional] 
**creator_users** | [**list[MinUserModel]**](MinUserModel.md) | All people who         are responsible for the creation of the collection. Data creators should receive credit         for their work and should therefore be included in the citation. | [optional] [default to []]
**creator_organisations** | [**list[OrganizationModel]**](OrganizationModel.md) | All         organisations who are responsible for the creation of the collection. Data creators should         receive credit for their work and should therefore be included in the citation. | [optional] [default to []]
**associate_users** | [**list[MinUserModel]**](MinUserModel.md) | Other person(s)         associated with the collection. | [optional] [default to []]
**associate_organisations** | [**list[OrganizationModel]**](OrganizationModel.md) | Other         organisation(s) associated with the collection. | [optional] [default to []]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


