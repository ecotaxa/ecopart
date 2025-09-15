# Constants

Values which can be considered identical over the lifetime of the back-end.
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**license_texts** | **dict(str, str)** | The supported licenses and help text/links. | [optional] 
**access** | **dict(str, str)** | Project access levels. | [optional] 
**app_manager** | **list[str]** | The application manager identity (name, mail), from config file. | [optional] [default to ["",""]]
**countries** | **list[str]** | List of known countries names. | [optional] [default to []]
**people_organization_directories** | **dict(str, str)** | Available directories to identify people and organizations in collections settings | [optional] 
**user_status** | **dict(str, int)** | Application User status values | [optional] 
**user_type** | **dict(str, str)** | Application User type values | [optional] 
**password_regexp** | **str** | 8 char. minimum, at least one uppercase, one lowercase, one number and one special char in &#39;#?!@%^&amp;*-+&#39;  | [optional] [default to '^(?:(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#?%^&*-+])).{8,20}$']
**email_verification** | **bool** | Require verification before activation. | [optional] [default to True]
**account_validation** | **bool** | Require validation by a Users Administrator before activation. | [optional] [default to False]
**short_token_age** | **int** | Email confirmation, password reset token lifespan. | [optional] [default to 1]
**profile_token_age** | **int** | Profile modification token lifespan. | [optional] [default to 24]
**recaptchaid** | **bool** | use Google ReCaptcha | [optional] [default to False]
**formulae** | **str** | Project default concentration formulae | [optional] [default to '''subsample_coef: 1/ssm.sub_part
total_water_volume: sam.tot_vol/1000
individual_volume: 4.0/3.0*math.pi*(math.sqrt(obj.area/math.pi)*ssm.pixel_size)**3''']
**default_project_access** | **str** | Project default access level | [optional] [default to '1']
**max_upload_size** | **int** | My Files max file upload size (bytes) | [optional] [default to 681574400]
**time_to_live** | **str** | My Files number of days before deleting directories | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


