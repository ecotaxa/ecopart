# GeneralExportReq

General purpose export request, produce a zip in a job with many options.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_id** | **int** | The Collection to export if requested. | [optional] 
**project_id** | [**AnyOfintegerstring**](AnyOfintegerstring.md) | The project(int) or projects (str, project ids list) to export. | 
**split_by** | [**ExportSplitOptionsEnum**](ExportSplitOptionsEnum.md) | If not none, separate (in ZIP sub-directories) output per given field. | [optional] 
**with_images** | [**ExportImagesOptionsEnum**](ExportImagesOptionsEnum.md) | Add in ZIP first (i.e. visible) image, all images, or no image.⚠️ &#39;all&#39; means maybe several lines per object in TSVs. | [optional] 
**with_internal_ids** | **bool** | Export internal database IDs. | [optional] [default to False]
**with_types_row** | **bool** | Add an EcoTaxa-compatible second line with types. | [optional] [default to False]
**only_annotations** | **bool** | Only save objects&#39; last annotation data. | [optional] [default to False]
**out_to_ftp** | **bool** | Copy result file to FTP area. Original file is still available. | [optional] [default to False]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


