# UserModelWithRights

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | The unique numeric id of this user. | 
**email** | **str** | User&#39;s email address, as text, used during registration. | 
**name** | **str** | User&#39;s full name, as text. | 
**organisation** | **str** | User&#39;s organisation name, as text. | [optional] 
**active** | **bool** | Whether the user is still active. | [optional] 
**country** | **str** | The country name, as text (but chosen in a consistent list). | [optional] 
**usercreationdate** | **datetime** | The date of creation of the user, as text formatted according to the ISO 8601 standard. | [optional] 
**usercreationreason** | **str** | Paragraph describing the usage of EcoTaxa made by the user. | [optional] 
**can_do** | **list[int]** | List of User&#39;s allowed actions : 1 create a project, 2 administrate the app, 3 administrate users, 4 create taxon. | [optional] [default to []]
**last_used_projects** | [**list[ProjectSummaryModel]**](ProjectSummaryModel.md) | List of User&#39;s last used projects. | [optional] [default to []]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


