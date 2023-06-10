Generates the code for a program description requested by the user using OpenAI API gpt-3.5-turbo and code-davinci-002 models.

Code changes/additions are added on a per-menu-request basis.

Selected log entries from running unit-tests and running the resulting program are sent to GPT for debug.

Project is work in progress.

Repo file structure (outdated):
```
.
├── file_management.py		#file management utilities
├── openai_params.py		
├── openai_requests.py		#build, receive and send requests
├── project					#dir: resulting scripts saved here
├── prompt_txt				#text prompt requests for openai model
│			├── clean_json_rq.py
│			├── error_hndl__logging_rq.py
│			├── input_and_argparse_rq.py
│			├── raw_code_rq.py
│			├── unittest_cli_comm_rq.py
│			├── docstrings_rq.py
│			├── debug_rq.py
│			├── custom_req.py
│			└── unittest_rq.py

├── README.md
├── requirements.txt
├── response_json			#dir: response json files
├── log_list_handler.py		#custom log handler
├── sample_self_config.py	#Sample: openai/azure models keys.
├── sg_utils.py				#request management utilities
└── simple_selfgen.py		#Menu block. Requires pointing scripts that import self_config.py (e.g sys.path.append) to dir where you save self_config.py
```
---------------------------------------------

Python v3.10+ required
Python required packages: See requirements.txt
Add this package to your sys.path

---------------------------------------------

Configuring OpenAI model and temperature per request:
For now these can be set for each request in function arguments:

Script: simple_selfgen.py
Functions:
	request_raw_code()
	request_code_enhancement()
	validate_and_clean_json()
Use Keyword Arguments for Functions:
	new_temp = 0.2
	new_engine = oai.codex_engine_deployment_name or oai.gpt_engine_deployment_name

---------------------------------------------

Updating the JSON file for Custom Requests:
Path to JSON: File/dir variables declared at file_management.py
Expected JSON structure: Flat no nesting.

---------------------------------------------