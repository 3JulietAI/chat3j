import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import List
import yaml
import nltk
from nltk import pos_tag
from nltk.chunk.regexp import RegexpParser
from nltk.tokenize import word_tokenize
from messages import format_chat_history


def stream_terminal_output(text: str, delay: float=0.05) -> None:
    """
    Print string one character at a time with a defined delay between characters. I do not like relying on streaming methods from completion endpoints. This is a better way to do it anyway. Agents can talk at different speeds depending on need and will be able to be changed en-chat with a parsed command (eventually)

    :param text: The string to print
    :param delay: The delay between printing each character
    :returns: Prints streaming text to terminal
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()  # Ensure char is displayed immediately
        time.sleep(delay)   # Wait a bit before printing the next one
    print()  # Move to the next line


def stream_agent_response(agent_name, text: str, delay: int) -> None:
    """
    Print string one character at a time.

    :param text: The string to print
    :param delay: The delay between printing each character
    :returns: Prints streaming text to terminal with Agent_Name prepended for terminal chat formatting.
    """
    sys.stdout.write(f"\n{agent_name}>> ")
    sys.stdout.flush()  # Flush to ensure bot_name is printed immediately

    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()  # Ensure char is displayed immediately
        time.sleep(delay)   # Wait a bit before printing the next one
    print()  # Move to the next line


def create_agent_structure(agent_name: str) -> None:
    """
    Create the agent directory structure and copy any template files needed.
    
    :param agent_name: The name of the agent
    :returns: Agent directory and instructions templates for mostly-semi-seamless integration
    """
    directories = [
        ''
    ]

    # because i .gitignore my projects directory for right now.
    agents_dir = Path('agents')
    if not agents_dir.exists():
        agents_dir.mkdir()
        print('----------------------------------------')
        print('Directory (agents) created')

    # Define target_dir
    target_dir = Path(f"agents/{agent_name}")
    if target_dir.exists():
        print("Name exists. Please try again with a new name.")
        return
    else:
    # Create the agent directory and subdirectories
        target_dir.mkdir(parents=True, exist_ok=True)
        for directory in directories:
            os.makedirs(os.path.join(f"agents/{agent_name}", directory), exist_ok=True)
        print('----------------------------------------')
        print('Agent structure created')

        # Copy the instruction template and other relevant templates like Modelfile. TODO: We can programatically update with argparse on exec if not defaults.
        shutil.copy("agents/agent_instuctions.yaml", f"{target_dir}/instructions.yaml")
        print(f"Copied agent instructions template to {target_dir}/instructions.yaml")

        print('----------------------------------------')
        print("All template files copied to new project")
    

def yml_load_agents_list() -> dict:
    """
    Load the projects from the YAML file into a Python dictionary.

    :returns: Dictionary of existing agents
    """
    agents_list_yaml_path=Path('agents/agents_list.yaml')
    if agents_list_yaml_path.exists():
        with open(agents_list_yaml_path, 'r') as file:
            return yaml.safe_load(file)
    return {'agents': []}


def print_dev_stamp(dev_stamp: str) -> None:
    """
    Purposeful re-use of stream_terminal_output to print the dev stamp so I don't have to type it out every time.

    :param dev_stamp: The dev stamp to stream.
    :returns: Prints streaming dev stamp to terminal
    """
    stream_terminal_output(dev_stamp, delay=0.05)


def stream_disco_def() -> None:
    """
    Streams the verbose definition of DISCO representing our DISCO project.. A closely related, yet to be disclosed project. Unless it has been and I forgot to update this docstring.

    :returns: Prints streaming DISCO definitions to terminal
    """
    stream_terminal_output("(D)irected (I)nformational (S)ecurity (CO)mpanion for: CHAT\nProject DISCO 2023-24", delay=0.02)


def print_main_banner() -> None:
    """
    Prints the main banner at init.

    :returns: Prints main banner to terminal
    """
    toilet_banner_plain("Welcome to")
    toilet_banner_metal("MOONBASE:\nCHAT")


def overwrite_yaml_with_literal_block(file_path: str, data_dict: dict) -> None:
    """
    Overwrite a YAML file with the contents of a dictionary, preserving multi-line strings.

    :param file_path: Path to the YAML file.
    :param data_dict: The dictionary containing the new data.
    """
    # Ensure the 'start_script' is treated as a literal block
    if 'start_script' in data_dict:
        data_dict['start_script'] = yaml.scalarstring.PreservedScalarString(data_dict['start_script'])

    with open(file_path, 'w') as file:
        yaml.safe_dump(data_dict, file, default_flow_style=False, allow_unicode=True)


def validate_function_return_type(function_name: str, return_value: str, expected_type: str) :
    """
    Validates the return value of a function.

    :param function_name: The name of the function.
    :param return_value: The return value of the function.
    :param expected_type: The expected type of the return value.
    """
    if not isinstance(return_value, expected_type):
        raise TypeError(f"Function {function_name} must return a {expected_type.__name__} object.")


def validate_function_return_format(function_name: str, return_value):
    """
    Function return value review prompt

    :param function_name: The name of the function.
    :param return_value: The return value of the function.
    :returns: My sanity during debugging.
    """
    
    print(f"=====  Validate return format of: {function_name}  =====")
    print(f"Return value:\n{return_value}\n")

    while True:
        user_response = input("Does the return meet your expectations? (y/n): ")
        if user_response.lower() == 'n' or user_response.lower() == 'no':
            print(f"=====!  {function_name}: FAILED  !=====")
            break
        elif user_response.lower() == 'y' or user_response.lower() == 'yes':
            print(f"=====!  {function_name}: PASSED  !=====")
            break
        else:
            print("Invalid response, please review the results and try again.")
            print(f"Return value:\n{return_value}\n")


def debug_print_function_return(function_name: str, return_value):
    """
    Debug print function return value

    :param function_name: The name of the function.
    :param return_value: The return value of the function.
    :returns: Prints the return value of a function to the terminal.
    """
    print(f"=====  DEBUG: {function_name}  =====")
    print(f"Return value:\n{return_value}\n")
    print(f"=====  END DEBUG: {function_name}  =====")
    

def parse_model_file(file_path):
    """
    * Modelfile parser
    Parse a Modelfile and return a dictionary of sections. Primarily intended for updates to the Modelfile. Not currently in use.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        if line.starstwith("FROM") or line.startswith("PARAMETER") or line.startswith("TEMPLATE") or line.startswith("SYSTEM") or line.startswith("LICENSE"):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line.split(' ')[0]
            current_content = [line] if current_section == "PARAMETER" else []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


def update_parameters(parameters):
    """
    * Modelfile editor
    Update the parameters in a Modelfile. Not currently in use.

    :param parameters: The parameters to update as list.
    """
    updated_params = []
    for param in parameters.split('\n'):
        if param.startswith("PARAMETER"):
            key, value = param.split(' ')[1:3]
            new_value = input(f"{key} ({value}): Enter new value or press enter to keep current: ").strip()
            updated_params.append(f"PARAMETER {key} {new_value if new_value else value}")
        else:
            updated_params.append(param)
    return '\n'.join(updated_params)


def toilet_banner_plain(text):
    """
    Toilet subprocess helper for simple pre-stylized banner for prettier outputs. -> Plain

    :param text: The text to bannerize.
    """
    banner = subprocess.run(['toilet', text], stdout=subprocess.PIPE)
    print(banner.stdout.decode('utf-8'))


def toilet_banner_metal(text):
    """
    Toilet subprocess helper for simple pre-stylized banner for prettier outputs. -> Metal

    :param text: The text to bannerize.
    :return: Print the bannerized text.
    """ 
    banner = subprocess.run(['toilet', '--filter', 'metal', text], stdout=subprocess.PIPE)
    print(banner.stdout.decode('utf-8'))


def toilet_banner_border_metal(text):
    """
    Toilet subprocess helper for simple pre-stylized banner for prettier outputs. -> Borderized:Metal
    """
    banner = subprocess.run(['toilet', '--filter', 'border:metal', text], stdout=subprocess.PIPE)
    print(banner.stdout.decode('utf-8'))


def message_cache_format_to_prompt(agent, message_history):
    chat_history = []
    for turn in message_history:
        turn_request = f"{agent.instructions.start_token}{turn.request.speaker} ({turn.request.timestamp}):\n{turn.request.content}{agent.instructions.end_token}\n"
        turn_response = f"{agent.instructions.start_token}{turn.response.speaker} ({turn.response.timestamp}):\n{turn.response.content}{agent.instructions.end_token}\n"
        chat_history.append(turn_request)
        chat_history.append(turn_response)
    chat_history = format_chat_history(chat_history)
    #print(f"\n{chat_history}")
    return chat_history


def chroma_results_format_to_prompt(chroma_results):
    if not chroma_results["documents"] or all(not doc for doc in chroma_results["documents"]):
        return "No results found."
    formatted_output = ""
    for result in chroma_results["documents"]:
        # Join the list into a string if the result is a list
        if isinstance(result, list):
            result = " ".join(result)

    # Split the result into components (sender, timestamp, message)
    components = result.split(" @ ")
    sender = components[0].strip()
    timestamp = components[1].strip()
    message = " @ ".join(components[2:]).strip()
    # Format each entry
    formatted_output += f"\n{sender} ({timestamp}):\n{message}"

    return formatted_output





def initialize_nltk_punkt_tagger():
    """
    Initialize the NLTK Punkt Tokenizer for sentence segmentation.
    """
    # Download the Punkt Tokenizer Models
    nltk.download('punkt')
    print("NLTK Punkt tokenizer downloaded.")
    nltk.download('averaged_perceptron_tagger')
    print("NLTK POS tagger downloaded.")
    