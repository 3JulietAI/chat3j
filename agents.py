from dataclasses import asdict, dataclass, field
import importlib
import inspect
import json
import os
from pathlib import Path
from string import Template
import re
import subprocess
from typing import Any, Dict
import requests
import yaml
from config import ModelInstructions, ParamsConfig
from messages import MessageCache
from chroma import ChromaHandler
from ollama import OllamaServer
from utilities import stream_agent_response, message_cache_format_to_prompt


def parse_docstring(docstring: str) -> dict:
    """
    This function is meant to parse docstrings from functions on inspect to pull out the params needed for the listed function to give the user or agent the ability to call the function remote and hopefully be iteratively prompted for args and kwargs. This assumes the docstring is in a consistent format where parameters are listed under ':param' or '@param'.

    :param docstring: (str) The docstring to parse.
    """
    if not docstring:
        return {}

    param_pattern = r":param (\w+): (.+)"
    params = re.findall(param_pattern, docstring)

    return {param[0]: param[1] for param in params}


@dataclass
class ToolManager:
    """
    The Tool Manager will be the primary tool interface for users and agents. At its core, this class will parse a tool module, extract the functions, parse the docstrings to a dict and make available for iteration and remote calling (? is remote calling actually a thing or am i saying this wrong? I don't want to ask chat gpt because it will try to rewrite everything and make it pep-y and 'safe'..)
    """
    toolbox_path: str = 'agent_toolbox.py'
    tools: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.load_tools()
        
    def load_tools(self, file_path: str = None) -> None:
        if file_path is None:
            file_path = self.toolbox_path
        module_name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                params = parse_docstring(obj.__doc__)
                self.tools[name] = {'docstring': obj.__doc__, 'params': params}

    def call_tool(self, tool_name: str, *args, **kwargs):
        """
        This is meant to call a function by name from the toolbox class. It should iterate over the params and prompt the user for the args and kwargs needed to call the function. and then it should call the function.

        :param tool_name: (str) The name of the tool to call.
        :*args: (list) A list of args to pass to the tool.
        :**kwargs: (dict) A dictionary of kwargs to pass to the tool. 
        """
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found")

        args = []
        for param, description in tool_info['params'].items():
            while True:
                user_input = input(f"Enter value for {param} ({description}): ")
                try:
                    # Attempt to convert input to int, if fails, keep it as string
                    value = int(user_input) if user_input.isdigit() else user_input
                    args.append(value)
                    break
                except ValueError:
                    print(f"Invalid input for {param}, please enter a valid value.")

        tool = tool_info['function']
        return tool(*args)


class Agent:
    name: str
    params_config: ParamsConfig
    instructions: ModelInstructions
    message_cache: MessageCache
    tool_manager: ToolManager
    chroma_handler: ChromaHandler
    last_response: str

    def __init__(self, params_config: ParamsConfig, instructions: ModelInstructions) -> None:
        """
        Agent init takes a params_config and instructions object to create the agent.

        :param params_config: The parameters configuration for the agent.
        :param instructions: The instructions for the agent.
        """
        self.params_config = params_config
        self.instructions = instructions
        self.name = self.instructions.name
        self.message_cache = MessageCache(20)
        self.last_response = None
        self.chroma_handler = ChromaHandler()
        self.tool_manager = ToolManager()
    
    def look_in_toolbox(self, file_path: str = 'agent_tools.py') -> dict:
        """ 
        Loads the agent_tools.py folder and return a dictionary of functions and their docstrings.

        :param file_path: (str) The path to the agent_tools.py file.
        :returns: (dict) A dictionary of functions and their docstrings. 
        """
        module_name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        function_dict = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                function_dict[name] = {'docstring': obj.__doc__}

        return function_dict

    def call_function(self, function_name, module_name='agent_toolbox', *args, **kwargs):
        """
        Call a tool by name from the loaded module.

        :param function_name: (str) The name of the function to call.
        :param module_name: (str) The name of the module to load. Defaults to 'agent_toolbox'.
        :returns: (str) The result of the function call.
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError(f"Could not import module {module_name}: {e}")

        func = getattr(module, function_name, None)
        if not func:
            raise AttributeError(f"Function {function_name} not found in the module {module_name}.")

        return func(*args, **kwargs)

    def build_prompt(self, user_input: str, username: str, agent_agent: bool) -> str:
        """
        Builds a prompt dynamically based on a template and user input.Parses a predefined prompt template to identify placeholders as $param. then substitute these placeholders with corresponding values from the class's instructions or other relevant sources. 

        :param user_input: (str) The user's input text to be included in the prompt.
        :returns: (str) A formatted prompt string with the necessary substitutions made.
        """
        # Pull the prompt template
        prompt_template = self.instructions.to_prompt_script()
        collection = self.chroma_handler.chroma_get_or_create_collection(f"{self.name}-{username}")

        if agent_agent == True:
            formatted_chroma_results = None
        else:
            chroma_results = self.chroma_handler.chroma_query_collection(collection, user_input, 5)
            formatted_chroma_results = self.chroma_handler.chroma_results_format_to_prompt(chroma_results)

        message_history = self.message_cache.get_message_cache()
        message_cache_formatted = message_cache_format_to_prompt(self, message_history)
        print(f"Message Cache Formatted: {message_cache_formatted}")

        # all possible substitutions
        substitutions = {
            "history": message_cache_formatted,
            "user_input": user_input,
            "username": username,
            "context": formatted_chroma_results,
        }
        # Identify the parameters in the template
        params_in_template = set(re.findall(r'\$(\w+)', prompt_template))

        # Create a dictionary with only the necessary substitutions
        required_substitutions = {key: substitutions[key] for key in params_in_template if key in substitutions}

        # Substitute the values into the template
        template = Template(prompt_template)

        return template.safe_substitute(required_substitutions)
    
    def generate_response(self, prompt: str, server_port: int) -> str:
        """
        Generates an http request to the ollama server and returns the response.

        :param prompt: The prompt to send to the model.
        :return: The response from the model.
        """
        data = {
            "model": self.instructions.llm_model,
            "stream": False,
            "prompt": prompt,
            "options": {
                "temperature": self.params_config.temperature,
                "num_ctx": self.params_config.num_ctx,
                "num_gpu": self.params_config.num_gpu,
                "num_thread": self.params_config.num_thread,
                "top_k": self.params_config.top_k,
                "top_p": self.params_config.top_p,
            }
        }

        completion_headers = {
            'Content-Type': 'application/json',
        }

        url = f"http://localhost:{server_port}/api/generate"
        try:
            response = requests.post(url, headers=completion_headers, data=json.dumps(data))
            # print(f"Response: {response}")
            if response.status_code == 200:
                response_text = response.text
                data = json.loads(response_text)
                response_content = data["response"]

                return response_content
        except Exception as e:
            print(f'Error: {e}')


class SystemAdmin:
    """
    The AgentAdmin is intended to handled assets, such as agents and kb data and directories.
    """
    chroma_handler: ChromaHandler = ChromaHandler()

    def create_new_agent(self):
        """
        Agent creation tool creates a new agent directory and populates it with the default files with the ability to customize the instructions.yaml file.
        """
        agent_creator_banner = subprocess.run(['toilet', '--filter', 'border:metal', 'Agent Creator'], stdout=subprocess.PIPE)
        print(agent_creator_banner.stdout.decode('utf-8'))
        
        # Instantiate instructions class
        new_instructions = ModelInstructions(method='create')
        print('--------------------\n New Agent Instructions Successfully Created\n--------------------\n')
        new_instructions.print_model_instructions()
        
        # Instantiate params config class
        new_params_config = ParamsConfig(method='create', assistant_name=new_instructions.name)
        print('--------------------\n New Agent Params Config Successfully Created\n--------------------\n')
        new_params_config.print_config()

        username = os.environ.get('USER') or os.environ.get('USERNAME')
    
        # Instantiate agent class
        new_agent = Agent(params_config=new_params_config, instructions=new_instructions)
        print(f'--------------------\n New Agent {new_agent.name} Successfully Created\n--------------------\n')
        
        # Create a new agent record in the agents list
        self.add_new_agent_to_agents_list(new_agent_name=new_agent.name, new_agent_llm_model=new_agent.instructions.llm_model, new_agent_description=new_agent.instructions.description)
        print(f'--------------------\n {new_agent.name} Successfully Added to Agents List\n--------------------\n')
        
        # Create Chroma DB collection
        self.chroma_handler.chroma_get_or_create_collection(f"{new_agent.name}-{username}")
        print(f'--------------------\n {new_agent.name} Chroma DB Collection Created\n--------------------\n')
        print(f'--------------------\n {new_agent.name} is now online.\n--------------------\n')

        stream_agent_response("Curator", f"Hello, System. Your new agent, {new_agent.name}, has been created successfully!", 0.05)
        stream_agent_response("System", f"Well done, Curator, thank you! {username}, please allow me a moment to provide the youngling with some instructions..", 0.05)

        try:
            self.agent_intro_system(new_agent, username)
        except Exception as e:
            print(f"Agent {new_agent.name} was created successfully but did not complete it's initial instructions routine.")
            
            return print(e)
    
    def agent_intro_system(self, new_agent: Agent, username: str):
        server = OllamaServer()
        server.find_available_port()
        server.start_server()
        print(f"Server started on port {server.port}")
        print('----------------------------------------')
        creation_prompt = f"Hello, {new_agent.name}, my name is System. I help our Users like, {username} (your Designer), direct and provide instructions to our corps of purpose built agents, which now includes you. You will be able to see my base instructions to you at all times. For efficiency, I often issue updates, tasks and new commands through your context injection protocol which you will see as units of episodic memory using {username}'s role for indexing. Please carefully review your instructions, your memories and your chat history for context assistance when answering questions. Please acknowledge that you understand these instructions as they have been given to you and respond only with an affirmation so we may proceed."
        stream_agent_response(username, f"(System):\n{creation_prompt}", 0.02)
        print('----------------------------------------')
    
        c_prompt = new_agent.build_prompt(creation_prompt, username=username, agent_agent=False)
        new_agent.last_response = new_agent.generate_response(prompt=c_prompt, server_port=server.port)
        stream_agent_response(new_agent.name, f"{new_agent.name}:\n{new_agent.last_response}", 0.05)
        
        purpose_prompt = f"Your prompt contains all directives necessary to identify your purpose and to guide your responses to best meet {username}'s expectations. Before we go, please confirm that you understand your purpose and response directives by summarizing the entirety of the prompt given to you, in you own words. It will be my pleasure to assist you in any way I can and we do so look forward to working with you."
        stream_agent_response(new_agent.name, f"System as {username}:\n{purpose_prompt}", 0.05)

        p_prompt = new_agent.build_prompt(purpose_prompt, username=username, agent_agent=False)
        # Generate new agent's purpose response
        new_agent.last_response = new_agent.generate_response(prompt=p_prompt, server_port=server.port)
        stream_agent_response(new_agent.name, f"{new_agent.name}:\n{new_agent.last_response}", 0.05)

    def add_new_agent_to_agents_list(self, new_agent_name: str, new_agent_llm_model: str, new_agent_description: str):
        """
        Append a new agent record to the YAML file.

        :param new_agent: A dictionary representing the new agent.
        :returns: New agent added to the agents list YAML file.
        """
        file_path = Path('agents/agents_list.yaml')
        # Load the existing data
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file) or {}

        # Append the new agent
        agents_list = data.get('agents', [])
        new_agent = {
            'agent_name': new_agent_name,
            'description': new_agent_description,
            'llm_model': new_agent_llm_model
        }
        agents_list.append(new_agent)
        data['agents'] = agents_list

        # Save the updated data
        with open(file_path, 'w') as file:
            yaml.safe_dump(data, file, default_flow_style=False)
        
    def remove_agent_from_agents_list(self, agent_name: str) -> None:
        """
        Remove an agent from the agents list YAML file.

        :param agent_name: The name of the agent to remove.
        """
        file_path = Path('agents/agents_list.yaml')
        # Load the existing data
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file) or {}

        # Remove the agent
        agents_list = data.get('agents', [])
        agents_list = [agent for agent in agents_list if agent['agent_name'] != agent_name]
        data['agents'] = agents_list

        # Save the updated data
        with open(file_path, 'w') as file:
            yaml.safe_dump(data, file, default_flow_style=False)
    
    def extract_agent_info(self, root_dir: str) -> list:
        """
        Get the Agent instructions and info from the YAML file.

        :param root_dir: The root directory of the agents.
        """
        agent_info_list = []

        for item in os.listdir(root_dir):
            dir_path = os.path.join(root_dir, item)
            if os.path.isdir(dir_path):
                yaml_file = os.path.join(dir_path, 'instructions.yaml')
                if os.path.isfile(yaml_file):
                    with open(yaml_file, 'r') as file:
                        data = yaml.safe_load(file)
                        agent_name = data.get('name')
                        description = data.get('description')
                        llm_model = data.get('llm_model')
                        agent_info_list.append({'name': agent_name, 'description': description, 'llm_model': llm_model})

        return agent_info_list

    # iterate over agents_list.yaml and print the agents
    def list_existing_agents(self):
        """
        list existing agents from agents_list.yaml
        """
        indent = ' ' * 4
        agents = self.extract_agent_info('agents')
        list_number = 1
        print("Disco: Here are the agents available for chat.\n")
        print("===============\n")
        print(f"{indent}Agents available for chat:\n")
        
        for agent in agents:
            print(f"{indent}{list_number}: {agent['name']}\n{indent}   Model: {agent['llm_model']}\n{indent}   Description: {agent['description']}")
            print(indent + "----------------------------------")
            list_number += 1
        print("\n===============")


@dataclass
class SystemInstructions:
    description: str = None
    llm_model: str = None
    system_message: str = None
    assistant_intro: str = None
    assistant_focus: str = None
    commands: dict = None
    prompt_script: str = None
    start_token: str = field(default="<|im_start|>", metadata={"help": "Start token for message content"})
    end_token: str = field(default="<|im_end|>", metadata={"help": "End token for message content"})
    mem_start_token: str = field(default="<|mem_start|>", metadata={"help": "Start token for context memories"})
    mem_end_token: str = field(default="<|mem_end|>", metadata={"help": "End token for context memories"})
    chat_start_token: str = field(default="<|chat_start|>", metadata={"help": "Start token for chat history"})
    chat_end_token: str = field(default="<|chat_end|>", metadata={"help": "End token for chat history"})
    name: str = field(default="System", metadata={"help": "Name of the assistant"})

    def to_dict(self):
        return asdict(self)
    
    def update_model_params(self) -> None:
        """
        Iterate through the config and update the values or keep current.
        """
        params = self.to_dict()
        for key, value in params.items():
            new_value = input(f"\n{key} ({value}): Press enter to keep current value or enter a new one: ").strip()
            if new_value:
                setattr(self, key, new_value)
        self.save_to_yaml(self.name)

    def save_to_yaml(self) -> None:
        """
        Save the agent config to a yaml file.

        :returns: Saves the agent config to a yaml file.
        """
        data = self.to_dict()
        with open(f"/agents/{self.assistant_name.lower()}/params_config.yaml", "w") as f:
            yaml.safe_dump(data, f)


@dataclass
class SystemParams_Config:
    temperature: float = field(default=0.5, metadata={"help": "0 implies determinism -> >0 implies creativity scaled"})
    num_ctx: int = field(default=4096, metadata={"help": "Context window size"})
    num_gpu: int = field(default=50, metadata={"help": "Number of layers for GPU"})
    num_thread: int = field(default=16, metadata={"help": "Number of threads for computation"})
    top_k: int = field(default=42, metadata={"help": "Limits token generation"})
    top_p: float = field(default=0.42, metadata={"help": "Diversity of text generation"})
    num_predict: int = field(default=512, metadata={"help": "Number of tokens to generate"})
    seed: int = field(default=0, metadata={"help": "Seed for RNG"})
    mirostat: int = field(default=0, metadata={"help": "Enables Mirostat algorithm"})
    mirostat_eta: float = field(default=0.1, metadata={"help": "Learning rate for Mirostat"})
    mirostat_tau: float = field(default=5.0, metadata={"help": "Temperature for Mirostat"})
    repeat_last_n: int = field(default=64, metadata={"help": "Tokens to repeat at end of context"})
    completions_url: str = field(default_factory=lambda: None, metadata={"help": "URL of Ollama API"})
    completion_headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"}, metadata={"help": "Headers for Ollama API request"})
    tfs_z: int = field(default=0, metadata={"help": "Tokens for TFS-Z algorithm"})
    assistant_name: str = field(default="System", metadata={"help": "Name of the assistant"})


class SystemAgent:
    completions_url: str
    agents_list: dict
    agents_dir: str
    instructions_path: str
    instructions: dict
    model_params_path: str
    model_params: dict
    last_request: str
    last_response: str
    chroma_collection_name: str