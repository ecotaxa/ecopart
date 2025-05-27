# SummaryExportReq

Summary export request.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_id** | **int** | The Collection to export if requested. | [optional] 
**project_id** | [**AnyOfintegerstring**](AnyOfintegerstring.md) | The project(int) or projects (str, project ids list) to export. | 
**quantity** | [**SummaryExportQuantitiesOptionsEnum**](SummaryExportQuantitiesOptionsEnum.md) | The quantity to compute. Abundance is always possible. | [optional] 
**summarise_by** | [**SummaryExportSumOptionsEnum**](SummaryExportSumOptionsEnum.md) | Computations aggregation level. | [optional] 
**taxo_mapping** | **dict(str, int)** | Mapping from present taxon (key) to output replacement one (value). Use a 0 replacement to _discard_ the present taxon. | [optional] 
**formulae** | **dict(str, str)** | Transitory: How to get values from DB free columns. Python syntax, prefixes are &#39;sam&#39;, &#39;ssm&#39; and &#39;obj&#39;.Variables used in computations are &#39;total_water_volume&#39;, &#39;subsample_coef&#39; and &#39;individual_volume&#39; | [optional] 
**out_to_ftp** | **bool** | Copy result file to FTP area. Original file is still available. | [optional] [default to False]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


