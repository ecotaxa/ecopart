# CollectionReq

update full or partial collection Request model
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external_id** | **str** | The external Id. | [optional] 
**title** | **str** | The collection title. | [optional] 
**short_title** | **str** | The collection short title. | [optional] 
**provider_user** | [**AnyOfintegerAnyType**](AnyOfintegerAnyType.md) | Id of the person who         is responsible for the content of this metadata record. Writer of the title and abstract. | [optional] 
**contact_user** | [**AnyOfintegerAnyType**](AnyOfintegerAnyType.md) | Id of the person who         should be contacted in cases of questions regarding the content of the dataset or any data restrictions.         This is also the person who is most likely to stay involved in the dataset the longest. | [optional] 
**project_ids** | **list[int]** | The list of composing project IDs. | [optional] 
**license** | [**LicenseEnum**](LicenseEnum.md) | The collection license. | [optional] 
**citation** | **str** | The collection citation. | [optional] 
**abstract** | **str** | The collection abstract. | [optional] 
**description** | **str** | The collection description. | [optional] 
**creator_users** | [**list[AnyOfintegerAnyType]**](AnyOfintegerAnyType.md) | List of users id&#39;s or dict with name, organization for external persons. | [optional] 
**associate_users** | [**list[AnyOfintegerAnyType]**](AnyOfintegerAnyType.md) | List of users id&#39;s or dict with name, organization for external persons. | [optional] 
**creator_organisations** | [**list[AnyOfintegerAnyType]**](AnyOfintegerAnyType.md) | All         organisations who are responsible for the creation of the collection. Data creators should         receive credit for their work and should therefore be included in the citation. | [optional] 
**associate_organisations** | [**list[AnyOfintegerAnyType]**](AnyOfintegerAnyType.md) | Other         organisation(s) Ids or names associated with the collection. | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


