# DarwinCoreExportReq

Darwin Core format export request, only allowed format for a Collection. @see https://dwc.tdwg.org/
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_id** | **int** | The collection to export, by its internal Id. | 
**dry_run** | **bool** | If set, then only a diagnostic of doability will be done. | [optional] [default to False]
**pre_mapping** | **dict(str, int)** | Mapping from present taxon (key) to output replacement one (value). Use a null replacement to _discard_ the present taxon. Note: These are EcoTaxa categories, WoRMS mapping happens after, whatever. | [optional] 
**include_predicted** | **bool** | If set, then predicted objects, as well as validated ones, will be exported. A validation status will allow to distinguish between the two possible statuses. | [optional] [default to False]
**with_absent** | **bool** | If set, then *absent* records will be generated, in the relevant samples, for categories present in other samples. | [optional] [default to False]
**with_computations** | [**list[SciExportTypeEnum]**](SciExportTypeEnum.md) | Compute organisms abundances (ABO), concentrations (CNC) or biovolumes (BIV). Several possible. | [optional] [default to []]
**formulae** | **dict(str, str)** | Transitory: How to get values from DB free columns. Python syntax, prefixes are &#39;sam&#39;, &#39;ssm&#39; and &#39;obj&#39;. Variables used in computations are &#39;total_water_volume&#39;, &#39;subsample_coef&#39; and &#39;individual_volume&#39; | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


