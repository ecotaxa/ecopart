# JobModel

All information about the Job.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**params** | [**object**](.md) | Creation parameters. | [optional] 
**result** | [**object**](.md) | Final result of the run. | [optional] 
**errors** | **list[str]** | The errors seen during last step. | [optional] [default to []]
**question** | [**object**](.md) | The data provoking job move to Asking state. | [optional] 
**reply** | [**object**](.md) | The data provided as a reply to the question. | [optional] 
**inside** | [**object**](.md) | Internal state of the job. | [optional] 
**id** | **int** | Job unique identifier. | 
**owner_id** | **int** | The user who created and thus owns the job.  | 
**type** | **str** | The job type, e.g. import, export...  | 
**state** | **str** | What the job is doing. Could be &#39;P&#39; for Pending (Waiting for an execution thread), &#39;R&#39; for Running (Being executed inside a thread), &#39;A&#39; for Asking (Needing user information before resuming), &#39;E&#39; for Error (Stopped with error), &#39;F&#39; for Finished (Done). | [optional] 
**step** | **int** | Where in the workflow the job is.  | [optional] 
**progress_pct** | **int** | The progress percentage for UI.  | [optional] 
**progress_msg** | **str** | The message for UI, short version.  | [optional] 
**creation_date** | **datetime** | The date of creation of the Job, as text formatted according to the ISO 8601 standard. | 
**updated_on** | **datetime** | Last time that anything changed in present line.  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


