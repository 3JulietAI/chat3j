import cmd2
from agents import SystemAdmin
from utilities import toilet_banner_metal
from chat import ChatHandler


def print_chat_menu():
    """
    Menu for the chat lobby. 
    """
    chat_menu_template = """
    _______________________________________________________

    Terminal: Chat Lobby

    [1] Chat Room: User > Agent
    [2] Chat Room: Agent > Agent
    [3] List Existing Agents
    [4] Create New Agent

    [9] Back to main menu (or type 'back' or 'main')

    _______________________________________________________
    """
    return print(chat_menu_template)


def print_chat_intro():
    print("\n\n")
    toilet_banner_metal("DISCO CHAT")
    print_chat_menu()


class ChatApp(cmd2.Cmd):
    def __init__(self):
        super().__init__()
        self.prompt = "3J:Chat>"
        self.intro = print_chat_intro()

    def do_1(self, line):
        print("Starting chat...")
        agent_name = input("Enter the name of the agent to chat with: ").lower()
        if agent_name == "back":
            print("Chat cancelled, here is the main menu...")
            print_chat_menu()
            return
        else:
            chat_handler = ChatHandler()
            chat_handler.chat_with_agent(agent_name)
            print_chat_menu()
    
    def do_2(self, line):
        try:
            chat_handler = ChatHandler()
            host_agent_name = input("Enter the name of the agent to host: ").lower()
            guest_agent_name = input("Enter the name of the agent to join: ").lower()
            chat_handler.multi_agent_chat(host_agent_name=host_agent_name, guest_agent_name=guest_agent_name)
            print_chat_menu()
        except Exception as e:
            print(f"Error: {e}")

    def do_3(self, line):
        print("\nGetting agent(s) info...")
        curator = SystemAdmin()
        curator.list_existing_agents()

    def do_4(self, line):
        print("\nAgent creator started...")
        curator = SystemAdmin()
        curator.create_new_agent()

    def do_9(self, line):
        print("\nHeading back to base...")
        return True
    
    def do_main(self, line):
        print("\nHeading back to base...")
        return True

    def do_back(self, line):
        print("\nHeading back to base...")
        return True  # Returning True exits the application
