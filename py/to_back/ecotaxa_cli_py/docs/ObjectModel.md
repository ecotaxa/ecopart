# ObjectModel

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**classif_when** | **datetime** | The human classification date, if **P** or **V**. | [optional] 
**classif_auto_id** | **int** | Set if the object was ever predicted, remains forever with these value. Reflect the &#39;last state&#39; only if classif_qual is &#39;P&#39;.  | [optional] 
**classif_auto_score** | **float** | Set if the object was ever predicted, remains forever with these value. Reflect the &#39;last state&#39; only if classif_qual is &#39;P&#39;. The classification auto score is generally between 0 and 1. This is a confidence score, in the fact that, the taxon prediction for this object is correct. | [optional] 
**classif_auto_when** | **datetime** | Set if the object was ever predicted, remains forever with these value. Reflect the &#39;last state&#39; only if classif_qual is &#39;P&#39;. The classification date. | [optional] 
**objid** | **int** | The object Id. | 
**acquisid** | **int** | The parent acquisition Id. | 
**classif_id** | **int** | The classification Id. | [optional] 
**objtime** | **str** |  | [optional] 
**latitude** | **float** | The latitude. | [optional] 
**longitude** | **float** | The longitude. | [optional] 
**depth_min** | **float** | The min depth. | [optional] 
**depth_max** | **float** | The min depth. | [optional] 
**objdate** | **date** |  | [optional] 
**classif_qual** | **str** | The classification qualification. Could be **P** for predicted, **V** for validated or **D** for Dubious. | [optional] 
**sunpos** | **str** | Sun position, from date, time and coords. | [optional] 
**classif_score** | **float** | The ML score for this object, if **P**. | [optional] 
**classif_who** | **int** | The user who manually classified this object, if **V** or **D**. | [optional] 
**orig_id** | **str** | Original object ID from initial TSV load. | 
**object_link** | **str** | Object link. | [optional] 
**complement_info** | **str** |  | [optional] 
**sample_id** | **int** | Sample (i.e. parent of parent acquisition) ID. | 
**project_id** | **int** | Project (i.e. parent of sample) ID. | 
**images** | [**list[ImageModel]**](ImageModel.md) | Images for this object. | [optional] [default to []]
**free_columns** | [**object**](.md) | Free columns from object mapping in project. | [optional] 
**classif_crossvalidation_id** | **int** | Always NULL, kept for compat. | [optional] 
**similarity** | **float** | Always NULL, kept for compat. | [optional] 
**random_value** | **int** | Random value associated to an image | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


