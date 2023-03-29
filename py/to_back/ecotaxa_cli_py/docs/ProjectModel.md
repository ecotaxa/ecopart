# ProjectModel

Basic and computed information about the Project.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**obj_free_cols** | **dict(str, str)** | Object free columns. | [optional] 
**sample_free_cols** | **dict(str, str)** | Sample free columns. | [optional] 
**acquisition_free_cols** | **dict(str, str)** | Acquisition free columns. | [optional] 
**process_free_cols** | **dict(str, str)** | Process free columns. | [optional] 
**bodc_variables** | **dict(str, str)** | BODC quantities from columns. Only the 3 keys listed in example are valid. | [optional] 
**init_classif_list** | **list[int]** | Favorite taxa used in classification. | [optional] [default to []]
**managers** | [**list[MinUserModel]**](MinUserModel.md) | Managers of this project. | [optional] [default to []]
**annotators** | [**list[MinUserModel]**](MinUserModel.md) | Annotators of this project, if not manager. | [optional] [default to []]
**viewers** | [**list[MinUserModel]**](MinUserModel.md) | Viewers of this project, if not manager nor annotator. | [optional] [default to []]
**instrument** | **str** | This project&#39;s instrument code. | [optional] 
**instrument_url** | **str** | This project&#39;s instrument BODC definition. | [optional] 
**contact** | [**MinUserModel**](MinUserModel.md) | The contact person is a manager who serves as the contact person for other users and EcoTaxa&#39;s managers. | [optional] 
**highest_right** | **str** | The highest right for requester on this project. One of &#39;Manage&#39;, &#39;Annotate&#39;, &#39;View&#39;. | [optional] [default to '']
**license** | [**LicenseEnum**](LicenseEnum.md) | Data licence. | [optional] 
**projid** | **int** | The project Id. | 
**title** | **str** | The project title. | 
**visible** | **bool** | The project visibility. | [optional] 
**status** | **str** | The project status. | [optional] 
**objcount** | **float** | The number of objects. | [optional] 
**pctvalidated** | **float** | Percentage of validated images. | [optional] 
**pctclassified** | **float** | Percentage of classified images. | [optional] 
**classifsettings** | **str** |  | [optional] 
**classiffieldlist** | **str** |  | [optional] 
**popoverfieldlist** | **str** |  | [optional] 
**comments** | **str** | The project comments. | [optional] 
**description** | **str** | The project description, i.e. main traits. | [optional] 
**rf_models_used** | **str** |  | [optional] 
**cnn_network_id** | **str** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


