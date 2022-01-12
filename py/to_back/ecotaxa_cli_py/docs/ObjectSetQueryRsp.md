# ObjectSetQueryRsp

Tuned model for faster serialization out. TODO: A bit useless in the context as FastAPI does _not_ use ser/deser from the model.       Instead, it produces what needs to be sent over the wire and calls a JSON encoder onto it.       So 1) It calls def jsonable_encoder (in FastAPI encoders.py)          2) It calls an encoder (presently ORJSONEncoder in main.py)
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


