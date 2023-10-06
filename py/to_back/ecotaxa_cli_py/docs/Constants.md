# Constants

Values which can be considered identical over the lifetime of the back-end.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**license_texts** | **dict(str, str)** | The supported licenses and help text/links. | [optional] 
**app_manager** | **list[str]** | The application manager identity (name, mail), from config file. | [optional] [default to ["",""]]
**countries** | **list[str]** | List of known countries names. | [optional] [default to []]
**user_status** | **dict(str, int)** | Application User status values | [optional] 
**password_regexp** | **str** | 8 char. minimum, at least one uppercase, one lowercase, one number and one special char in &#39;#?!@%^&amp;*-&#39;  | [optional] [default to '^(?:(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#?%^&*-+])).{8,20}$']
**email_verification** | **bool** | Require verification before activation. | [optional] [default to True]
**account_validation** | **bool** | Require validation by a Users Administrator before activation. | [optional] [default to False]
**short_token_age** | **int** | Email confirmation, password reset token lifespan. | [optional] [default to 1]
**profile_token_age** | **int** | Profile modification token lifespan. | [optional] [default to 24]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


