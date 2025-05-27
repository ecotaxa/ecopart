# ClassifyAutoReqMult

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**target_ids** | **list[int]** | The IDs of the target objects. | 
**classifications** | **list[list[int]]** | The wanted new classifications, i.e. taxon ID, one list for each object. | 
**scores** | **list[list[float]]** | The classification scores, between 0 and 1. Each indicates the probability that the taxon prediction of this object for this category is correct. | 
**keep_log** | **bool** | Set if former automatic classification history is needed. Deprecated, always True. | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


