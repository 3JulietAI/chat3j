import sys
import cmd2
from chat_cli import ChatApp
from agent_library_cli import AgentsLibCli
from ollama_cli import OllamaApp
from utilities import stream_agent_response, stream_disco_def, print_main_banner, print_dev_stamp
from agents import Agent


def print_main_menu():
    """
    Pretty sure the name says it all on this one but here is a docstring to appease the linting gods..
    """
    menu_template = """
    _______________________________________________________

    Terminal: Main

    [1] Chat Lobby
    [2] Agents Library
    [3] Ollama Library
    [4] Games Lobby
    
    [9] Exit

    _______________________________________________________
    """
    return print(menu_template)


def main_intro():
    stream_disco_def()
    print_main_banner()
    print_dev_stamp("3Juliet, AI by @technomoonbase (2023)")
    print_main_menu()


def child_break_banner():
    print("\n\n")
    print("3Juliet, AI: @technomoonbase (2023)")
    print_main_menu()


class Main(cmd2.Cmd):
    """
    The primary command line interface for the Moonbase Chat application and the main menu interface.

    """
    prompt = "3J:Moonbase> "
    intro = main_intro()

    def do_1(self, line):
        print("Entering chat lobby...")
        chat_app = ChatApp()
        chat_app.cmdloop()
        child_break_banner()
    
    def do_2(self, line):
        print("Entering agents library...")
        agents_app = AgentsLibCli()
        agents_app.cmdloop()
        child_break_banner()
    
    def do_3(self, line):
        print("Entering Ollama library...")
        ollama_app = OllamaApp()
        ollama_app.cmdloop()
        child_break_banner()
    
    def do_4(self, line):
        """
        AI Odyssey (2024) - text-based adventure game
        AI Ships (2023-24) - just another battleship game
        """
        pass        
    
    def do_5(self, line):
        pass
    
    def do_6(self, line):
        child_break_banner()
    
    def do_9(self, line):
        print("Exiting...")
        sys.exit(0)

    def do_exit(self, line):
        print("Exiting...")
        return True  # Returning True exits the application

    def do_help(self, line):
        print("\n\nGreetings, this is a recorded announcement as we are all out at the moment. The Program Devlopment Council of 3Juliet thanks you for your esteemed visit but regrets that the entire base helpdesk is temporarily closed. If you would like to leave your name, and a communications device on which you can be contacted, please kindly do so at the tone.\n\n")
        your_name, your_com = input("Name: "), input("Your chosen method of communication: ")
        print(f"\n\nThank you, {your_name}. Your message has been disregarded. We will not contact you at any point. We do thank you again for your enthusiasm and hope that you are able to find your way eventually. Goodbye.\n\n")
        print_dev_stamp("Base Chat by 3Juliet, AI:@technomoonbase (2023)")
        print_main_menu()
        intro = "Welcome to Base Chat by 3Juliet! Type ? for help"

if __name__ == '__main__':
    app = Main()
    app.cmdloop()
