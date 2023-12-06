from dataclasses import dataclass
import socket
import subprocess


@dataclass
class OllamaServer:
    """
    Ollama server class. Starts and stops the Ollama server after finding and assigning an available port.
    """
    process = None
    port: int = 11434 # default1 ollama server port

    def start_server(self):
        """
        Starts the Ollama server on the super's port.

        :returns: None
        """
        #command = f"OLLAMA_HOST=localhost:{self.port} ollama serve"
        self.port = self.find_available_port()
        command = f"ollama serve"
        try:
            self.process = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print(f"Ollama server started on port {self.port}")
        except Exception as e:
            print(f"Error starting Ollama server on port {self.port}: {e}")

    def stop_server(self):
        """
        Stops the Ollama server.
        """
        if self.process is None:
            print("No server process to stop.")
            return

        # Gracefully terminate the process
        #self.process.terminate() # it seems my kernel is struggling with grace so we will need to be a bit more forceful up front for now.
        self.process.kill()
        # Wait for a bit to see if it shuts down
        try:
            self.process.wait(timeout=5)  # Wait for 5 seconds
        except subprocess.TimeoutExpired:
            print("Server did not terminate gracefully, forcefully stopping it.")
            self.process.kill()

        print("Server process stopped.")
        self.process = None

    def find_available_port(self, start_port=4200, end_port=4300):
        """
        This functions searches a preset range of ports for an available port to use for the Ollama server.

        :param start_port: The first port to check.
        :param end_port: The last port to check.
        :returns: The first available port in the range.
        """
        for port in range(start_port, end_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    self.port = port
                    return
                except socket.error:
                    continue
        raise ValueError(f"No available ports found in the range {start_port}-{end_port}")


class OllamaClient:
    def __init__(self, port: int = 11434):
        self.port = port

    def ollama_pull_model(model_name: str) -> None:
        """
        Download a model from the Ollama server.

        :param model_name: The name of the model to download.
        """
        subprocess.run(['ollama', 'pull', model_name])

    # remove model
    def ollama_remove_model(model_name: str) -> None:
        """
        Remove a model from your local Ollama repo.

        :param model_name: The name of the model to remove.
        """
        subprocess.run(['ollama', 'rm', model_name])

    # copy model
    def ollama_copy_model(src_model_name: str, dest_model_name: str) -> None:
        """
        Copies a model from one name to another. Intended for use during fine-tuning or new model creation.

        :param src_model_name: The name of the model to copy.
        :param dest_model_name: The name of the new model.
        """
        subprocess.run(['ollama', 'cp', src_model_name, dest_model_name])

    # create model from Modelfile
    def ollama_create_model_from_modelfile(model_name: str) -> None:
        """
        Uses the Modelfile to create a new model.

        :param model_name: The name of the model to create.
        """
        with open(f'agents/{model_name}/Modelfile', 'w') as f:
            modelfile = f.read()
        subprocess.run(['ollama', 'create', model_name])


    def ollama_list_downloaded_models() -> None:
        """
        Lists all the models you have downloaded from the Ollama server.
        """
        subprocess.run(['ollama', 'list'])