api_farm
========

Simple workers farm with API

Implementation of simple task manager flow. Workers farm based on Celery/Django with REST JSON API. Set Celery's concurrency param to manage number of workers.
Initial authorisation is based on django-registration, after user is created - he gets secret API_ID for API authorisation.
After logging in - user can see his Profile page where he can start workers, see current workers/results, generate new API_ID secret.

POST /start_task/
========
Parameters: api_id=api-id & json={"tasks": [ { "task": ["message1_1", "message1_2"] } ] }

Request to start one or several tasks. Param validation for this request:
1) total length of JSON parameters <= MAX_JSON
2) total number of concurrent tasks <= MAX_TASKS
3) number of messages per one task <= MAX_MESSAGES
4) every message length <= MAX_MSG_LEN

For each task - a new record in Task is created, and task unique_id is returned.
Every worker gets task ID to refresh it's status, and messages list in JSON.
If task gets error during the task.delay() call (state=FAILURE) - the DB task record is updated with status=100 and error_msg with error text.

GET /get_status/
========
Parameters: api_id=api-id & unique_id=[id1]...unique_id=[idN]

Returns task statuses for provided list of task unique IDs. If there is no task on some unique IDs - errors for these one.

GET /get_result/
========
Parameters: api_id=api-id & unique_id=[id1]...unique_id=[idN]

Returns the list of tasks' results for provided list of task unique IDs. If there is no task on some unique IDs - errors for these one.

GET /my_tasks/
========
Parameters: api_id=api-id [& show_all=1]

Returns the list of all tasks with statuses PENDING/STARTED for current user (owner of secret API_ID).
If called with show_all=1 - returns tasks with all statuses including finished successfully and failed.
