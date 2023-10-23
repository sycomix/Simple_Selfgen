#!/usr/bin/env python3

# import libraries
import os
import threading
import json
import dataclasses
import user_interaction as uinteraction
import log_list_handler
#import tools
import tools.file_management as fm
import tools.request_utils as ut
# import openai libs/modules
import openai_params as oai
import config_dir.config as config

class Feature_Common:
    # show request text on screen
    show_request = True

    # set model and temp
    model = oai.primary_engine_deployment_name
    model_temp = 0.7

    # program description
    program_description = None

    def __init__(self, program_description=None):
        self.cum_tokens = 0
        # set common instances
        self.user_interaction_instance = None
        self.set_user_interaction_instance(uinteraction.User_Interaction())
        #self.log_list_handler_instance = None
        self.logger_instance = None
        self.log_list_handler_instance = None
        self.set_log_list_handler_instance(log_list_handler.config_custom_logger())
        #set prog desc
        if program_description is not None:
            self.program_description = program_description
        #init responses
        self.gpt_response = None

    def set_user_interaction_instance(self, user_interaction_instance):
        self.user_interaction_instance = user_interaction_instance

    def set_log_list_handler_instance(self, log_list_handler_instance):
        self.logger_instance, self.log_list_handler_instance = log_list_handler_instance

    #request module code
    def send_request(self, sys_mssg, request_to_gpt, summary_new_request):
        clean_response = None
        this_conversation = []

        # start timer
        stop_event = threading.Event()
        thread = threading.Thread(target=ut.spinning_timer, args=("Awaiting Response...", stop_event))
        thread.start()
        try:
            if oai.used_api == oai.Model_API.AZURE_OPENAI_API:
                if self.model[1] == 'gpt-3.5-turbo-0301':
                    system_message = {"role": "system", "content": sys_mssg}
                    this_conversation.extend(
                        (
                            system_message,
                            {"role": "user", "content": request_to_gpt},
                        )
                    )
                    request_tokens = this_conversation_tokens = ut.num_tokens_from_messages(this_conversation)
                    ut.token_limit(request_tokens)
                    self.cum_tokens += this_conversation_tokens

                    self.print_request_information(summary_new_request, request_tokens, sys_mssg, request_to_gpt)
                    response = oai.openai.ChatCompletion.create(
                        engine=self.model[0],
                        messages=this_conversation,
                        temperature=self.model_temp,
                        max_tokens=config.max_response_tokens,
                    )
                    clean_response = response['choices'][0]['message']['content'].replace("'''", "'").replace('"""','"').replace('```', '`')
                    this_conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})

                elif self.model[1] in ['code-davinci-002', 'text-davinci-003']:
                    model_prompt = f"#####Fix bugs in the below module\n###Buggy {config.program_language}\n{ut.get_response_value_for_key(self.gpt_response, config.code_key_in_json)}###Fixed {config.program_language}"

                    this_conversation.append({"role": "user", "content": model_prompt})
                    request_tokens = this_conversation_tokens = ut.num_tokens_from_messages(this_conversation)
                    ut.token_limit(request_tokens)
                    self.cum_tokens += this_conversation_tokens

                    self.print_request_information(summary_new_request, request_tokens, None, model_prompt)
                    response = oai.openai.Completion.create(
                        engine=self.model[0],
                        prompt=model_prompt,
                        temperature=self.model_temp,
                        max_tokens=config.max_response_tokens,
                        stop=["###"]
                    )
                    for choice in response.choices:
                        if "text" in choice:
                            clean_response = json.dumps({"module":choice.text}) #string
                            this_conversation.append({"role": "assistant", "content": choice.text})

        except Exception as e:
            print(f"OpenAI API returned an API Error:\n{e}")

        # stop timer
        stop_event.set()
        thread.join()
        print('\r\033[K', end='')  # Clear the line

        this_conversation_tokens = ut.num_tokens_from_messages(this_conversation)
        self.cum_tokens += this_conversation_tokens

        ut.token_limit(this_conversation_tokens)

        print("-" * 40)
        try:
            pretty_json_response = json.dumps(json.loads(clean_response), indent=2,separators=(',', ':'))
            print(f"\n\033[1;92mResponse: CumTokens:{self.cum_tokens} RespTokens:{this_conversation_tokens}\n\033[0m\033[92m{pretty_json_response}\n\033[0m")
        except Exception as e:
            print(f"Exception on JSON Received: {e}: {clean_response:<10} \n")
            #print("RAW response:", clean_response)
            print("-" * 40)
            # JSON response invalid re-request or quit
            return False

        self.gpt_response = json.loads(clean_response)  # .strip("\n")  #.replace('```', '')

        return True

    def print_request_information(self, summary_new_request, request_tokens, sys_mssg, message_or_prompt):
        print();print("-" * 40);print()
        print(f"\033[44;97mJob Request: {summary_new_request}\033[0m")

        if self.show_request:
            if sys_mssg is not None:
                print(f"\n\033[1;97mRequest: CumTokens:{self.cum_tokens} Req_Tokens:{request_tokens}\033[0m: System Message:{sys_mssg}\nPrompt:{message_or_prompt}")
            else:
                print(
                    f"\n\033[1;97mRequest: CumTokens:{self.cum_tokens} Req_Tokens:{request_tokens}\033[0m: \nPrompt:{message_or_prompt}")
        else:
            print(f"\n\033[1;97mRequest Sent: CumTokens:{self.cum_tokens} Req_Tokens:{request_tokens}\033[0m")

        print()
        print(f"\033[1;97mModel Settings:\033[0m Engine: {self.model[1]}, Temperature: {self.model_temp}")

    def build_request_args(self, summary_new_request, sys_mssg, request_to_gpt):
        return summary_new_request, sys_mssg, request_to_gpt

    # manage request
    def request_code_enhancement(self, request_args):
        # unpack request args for clarity. pass request_to_gpt to change value for utests and standard
        summary_new_request, sys_mssg, request_to_gpt = request_args
        # send request to model
        return self.send_request(sys_mssg, request_to_gpt, summary_new_request)

    @staticmethod
    def valid_response_file_management(filename, full_path_dir, gpt_response, success_mssg=None):
        if success_mssg is not None:
            print(f"\033[43m{success_mssg}\033[0m")
        # version and save
        fm.version_file(full_path_dir, filename, full_path_dir)
        fm.get_dict_value_save_to_file(gpt_response, config.initial_dir, filename, "#!/usr/bin/env python3\n\n")
        print(f"Code:\n", fm.get_code_from_dict(gpt_response, config.code_key_in_json))

        # TODO: remove for debugging
        # fm.write_to_file(self.json_fname, self.json_dirname, gpt_response, "w")
        # end remove for debugging

    def get_file_path_from_user(self, mssg):
        while True:
            full_path_to_file = self.user_interaction_instance.request_input_from_user(mssg)
            if not fm.validate_filepath(full_path_to_file):
                continue
            else:
                return full_path_to_file

    @staticmethod
    def read_code_from_file(full_path_to_script):
        return fm.read_file_stored_to_buffer(
            os.path.basename(full_path_to_script),
            os.path.dirname(full_path_to_script),
        )
