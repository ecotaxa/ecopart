# ObjectSetQueryRsp

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**object_ids** | **list[int]** | Matching object IDs. | [optional] [default to []]
**acquisition_ids** | **list[int]** | Parent (acquisition) IDs. | [optional] [default to []]
**sample_ids** | **list[int]** | Parent (sample) IDs. | [optional] [default to []]
**project_ids** | **list[int]** | Project Ids. | [optional] [default to []]
**details** | **list[list[object]]** | Requested fields, in request order. | [optional] [default to []]
**total_ids** | **int** | Total rows returned by the query, even if it was window-ed. | [optional] [default to 0]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


