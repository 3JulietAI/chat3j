from dataclasses import dataclass, asdict, field
from pathlib import Path
import yaml
import os
import shutil


@dataclass
class ModelInstructions:
    """
    Agent configuration dataclass for managing prompts and messaging to the agent.
    """
    name: str = None
    description: str = None
    llm_model: str = None
    system_message: str = None
    assistant_intro: str = None
    assistant_focus: str = None
    commands: dict = None
    prompt_script: str = None
    start_token: str = None
    end_token: str = None
    mem_start_token: str = None
    mem_end_token: str = None
    chat_start_token: str = None
    chat_end_token: str = None
    completions_url: str = None

    def __init__(self, method: str, assistant_name: str = None) -> None:
        """
        Model instructions init takes a method param as ['create', 'load'] to determine if the instructions should be loaded from a yaml file or created from the CLI.

        :param method: The method to use to create the instructions.
        """
        if method == 'load':
            if assistant_name:
                self.load_from_yaml(assistant_name)
                print(f"Loaded instructions for {self.name}")
                print(asdict(self))
            else:
                print("Error: No assistant name provided.")    
        elif method == 'create':
            self.load_defaults_from_yaml()
            print("Creating new assistant instructions...")
            customize = input("Would you like to customize the instructions? (y/n): ").strip()
            if customize == 'y':
                instructions = self.to_dict()
                for key, value in instructions.items():
                    new_value = input(f"\n{key} ({value}): Press enter to keep current value or enter a new one: ").strip()
                    if new_value:
                        setattr(self, key, new_value)
                print(asdict(self))
            else:
                print("Using default instructions. You can customize these later.")
                print(asdict(self))
            
            # Create the agent directories and populate them with the default files
            agents_dir = Path('agents/')
            templates_dir = Path('agent-templates/')
            templates = [file for file in templates_dir.iterdir() if file.suffix in ['.md', '.yml', '.yaml', '.txt']]
            # this gives the ability to default specifically named blank files and types for template inclusion
            include_files = []  

            directories = [
                'fine-tuning'
            ]

            try:
                print('Checking for agents directory...')
                if not agents_dir.exists():
                    os.mkdir(agents_dir)
                    print('----------------------------------------')
                    print('Directory (agents) created')
                
                print('Cross-checking for existing agents...')
                target_agent_dir = Path(f'agents/{self.name.lower()}')
                if target_agent_dir.exists():
                    print('----------------------------------------')
                    print(f'Agent ({self.name}) already exists. Pleae choose another name.')
                    return None
                else:
                    print('Agent does not exist, creating...')
                    target_agent_dir.mkdir(parents=True, exist_ok=True)
                    print('----------------------------------------')
                    print(f'Agent Directory ({self.name}) created')

                for directory in directories:
                    Path(f'agents/{self.name.lower()}/{directory}').mkdir(parents=True, exist_ok=True)
                    print('----------------------------------------')
                    print(f'Agent Sub-Directory ({self.name}/{directory}) created')
                
                # Copy the project template files
                for template in templates:
                    shutil.copy(template, f"{agents_dir}/{self.name.lower()}/{template.name}")
                    print(f"Copied {template} to {agents_dir}/{self.name.lower()}/{template.name}")

                print('----------------------------------------')
                print("All template files copied to new project")
                print('----------------------------------------')

                self.save_to_yaml()

            except Exception as e:
                print(e)
                return


    def to_dict(self) -> dict:
        """
        Export config class to a base dict

        :returns: Base dictionary for the config class.
        """
        return asdict(self)
    
    def print_model_instructions(self) -> None:
        """
        Print the config to the terminal.

        :returns: Prints a pre-defined config string to the terminal.
        """
        print(f"Agent Configuration:\n{self.to_dict()}")
    
    def to_prompt_script(self) -> str:
        """
        Export config class to a base dict

        :returns: Base dictionary for the config class.
        """
        return (
            f"{self.start_token}System: \n"
            f"{self.system_message}{self.end_token}\n"
            f"{self.start_token}Assistant: \n"
            f"{self.assistant_intro}{self.end_token}\n"
            f"{self.start_token}User: \n"
            f"Your current focus should be: {self.assistant_focus}{self.end_token}\n"
            f"{self.mem_start_token}Context from memory: "
            f"$context{self.mem_end_token}\n"
            f"Chat History: \n"
            f"$history\n"
            f"{self.start_token}$username: \n"
            f"$user_input{self.end_token}\n"
            f"{self.start_token}{self.name}: \n"
        )
    
    def update_model_instructions(self) -> None:
        """
        Iterate through the config and update the values or keep current.
        """
        instructions = self.to_dict()
        for key, value in instructions.items():
            new_value = input(f"\n{key} ({value}): Press enter to keep current value or enter a new one: ").strip()
            if new_value:
                setattr(self, key, new_value)
        self.save_to_yaml()
    
    def load_defaults_from_yaml(self) -> None:
        """
        Load the agent instructions config from a yaml file.
        """
        model_instructions = Path(f"agent-templates/instructions.yaml")
        if model_instructions.exists():
            with model_instructions.open('r') as file:
                instructions = yaml.safe_load(file)
                for key, value in instructions.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

    def load_from_yaml(self, assistant_name: str) -> None:
        """
        Load the agent instructions config from a yaml file.
        """
        model_instructions = Path(f"agents/{assistant_name.lower()}/instructions.yaml")
        if model_instructions.exists():
            with model_instructions.open('r') as file:
                instructions = yaml.safe_load(file)
                for key, value in instructions.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
    
    def save_to_yaml(self) -> None:
        """
        Save the agent config to a yaml file.

        :returns: Saves the agent config to a yaml file.
        """
        data = self.to_dict()
        with open(f"agents/{self.name.lower()}/instructions.yaml", "w") as f:
            yaml.safe_dump(data, f)


@dataclass
class ParamsConfig:
    """
    Agent configuration dataclass for tweaking completion parameters. More are available through Ollama's API, I will build this out to cover it all eventually. Parameter definitions from Ollama and their defaults values are given in params. Class field defaults are values that I have found to work well for my use cases.

    :param temperature: The temperature of the model. Increasing the temperature will make the model answer more creatively. (Default: 0.8)
    :param num_ctx: Sets the size of the context window used to generate the next token. (Default: 4096)
    :param num_gpu: The number of layers to send to the GPU(s). On macOS it defaults to 1 to enable metal support, 0 to disable. (Default: 50)
    :param num_thread: Sets the number of threads to use during computation. By default, Ollama will detect this for optimal performance. It is recommended to set this value to the number of physical CPU cores your system has (as opposed to the logical number of cores). (Default: 8, I run 16 on a core i9)
    :param top_k: Reduces the probability of generating nonsense. A higher value (e.g. 100) will give more diverse answers, while a lower value (e.g. 10) will be more conservative. (Default: 40)
    :param top_p: Works together with top-k. A higher value (e.g., 0.95) will lead to more diverse text, while a lower value (e.g., 0.5) will generate more focused and conservative text. (Default: 0.9)
    :param num_predict: The number of tokens to generate. (Default: 128)
    :param seed: The seed to use for random number generation. (Default: 0)
    :param mirostat: Enables the Mirostat algorithm. (Default: 0)
    :param mirostat_eta: The learning rate for the Mirostat algorithm. (Default: 0.1)
    :param mirostat_tau: The temperature for the Mirostat algorithm. (Default: 5.0)
    :param repeat_last_n: The number of tokens to repeat at the end of the context. (Default: 64)
    :param completions_url: The URL of the Ollama API endpoint.
    :param completion_headers: The headers to send with the request to the Ollama API.
    :param start_token: The token to use to start the prompt.
    :param end_token: The token to use to end the prompt.
    :param tfs_z: The number of tokens to use for the TFS-Z algorithm. (Default: 0)
    :creates: Param config object for the agent.
    """
    temperature: float = None
    num_ctx: int = None
    num_gpu: int = None
    num_thread: int = None
    top_k: int = None
    top_p: float = None
    num_predict: int = None
    seed: int = None
    mirostat: int = None
    mirostat_eta: float = None
    mirostat_tau: float = None
    repeat_last_n: int = None
    tfs_z: int = None
    assistant_name: str = None

    def __init__(self, method: str, assistant_name: str) -> None:
        """
        Model Params Config init takes a method param as ['create', 'load'] to determine if the instructions should be loaded from a yaml file or created from the CLI.

        :param method: The method to use to create the instructions.
        """
        self.assistant_name = assistant_name
        if method == 'load':
            self.load_from_yaml()
            print(f"Loaded param config for {assistant_name}")
            print(asdict(self))
        elif method == 'create':
            self.load_defaults_from_yaml()
            print("Creating new completion parameters configuration...")
            customize = input("Would you like to customize the model params? (y/n): ").strip()
            if customize == 'y':
                self.update_model_params()
                print(asdict(self))
            else:
                print("Using default completion parameters. You can customize these later.")
                print(asdict(self))
        else:
            print("Error: Invalid method. Please use 'create' or 'load'.")
    
    def to_dict(self) -> dict:
        """
        Export config class to a base dict

        :returns: Base dictionary for the config class.
        """
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
        self.save_to_yaml(self.assistant_name)
    
    def print_config(self) -> None:
        """
        Print the config to the terminal.

        :returns: Prints a pre-defined config string to the terminal.
        """
        print(f"Agent Configuration:\n{self.to_dict()}")
    
    def cli_create_config(self) -> None:
        """
        Create a config from the CLI.
        """
        params = self.to_dict()
        for key, value in params.items():
            new_value = input(f"\n{key} ({value}): Press enter to keep current value or enter a new one: ").strip()
            if new_value:
                params[key] = new_value
    
    def load_from_yaml(self) -> None:
        """
        Load the agent instructions config from a yaml file.
        """
        params_config = Path(f"agents/{self.assistant_name.lower()}/params_config.yaml")
        if params_config.exists():
            with params_config.open('r') as file:
                completion_params = yaml.safe_load(file)
                for key, value in completion_params.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
    
    def load_defaults_from_yaml(self) -> None:
        """
        Load the agent instructions config from a yaml file.
        """
        params_config = Path(f"agent-templates/params_config.yaml")
        if params_config.exists():
            with params_config.open('r') as file:
                completion_params = yaml.safe_load(file)
                for key, value in completion_params.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
    
    def save_to_yaml(self) -> None:
        """
        Save the agent config to a yaml file.

        :returns: Saves the agent config to a yaml file.
        """
        data = self.to_dict()
        with open(f"/agents/{self.assistant_name.lower()}/params_config.yaml", "w") as f:
            yaml.safe_dump(data, f)
