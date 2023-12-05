from datetime import datetime
import os
from uuid import uuid4
from agents import Agent
from chroma import ChromaHandler
from config import ModelInstructions, ParamsConfig
from messages import Message, Turn, start_new_conversation
from ollama import OllamaServer
from utilities import debug_print_function_return, stream_agent_response, toilet_banner_metal, toilet_banner_plain


class ChatHandler:
    """
    With multiple chat formats, it makes sense to kick this to it's own class to keep things tidy. Supports User>Agent chat and Agent>Agent chat currently. Looking at integrating a pub sub library so num of participants is arbitrary. The logic for round robin with agents is a little trickier to flesh out and maintain a consistent flow. Agent>Agent chat still tends to convert to mimicry after 12 to 15 rounds but i am hoping improvements in source will fix this along with logic to filter, limit or remove chroma results from prompt which has shown good results in testing but limits the functionality and overall scope.
    """
    chroma_handler: ChromaHandler = ChromaHandler()

    def chat_with_agent(self, assistant_name: str) -> None:
        """
        Opens a chat session and starts a new conversation with the selected agent. Chroma collection is created with agent:user nomencalture to refine results. This function uses exec through the OllamaServer instance to find available ports and start a server on that port. The server is stopped when the chat session ends. 

        :param project: The name of the project to chat about. If None, chat about all projects.
        """
        instructions = ModelInstructions(method='load', assistant_name=assistant_name)
        
        config = ParamsConfig(method='load', assistant_name=assistant_name)
        
        agent = Agent(params_config=config, instructions=instructions)

        # Start a new conversation for chat logging. TODO: ability to check existing conversations and load OR new
        conversation = start_new_conversation(host=agent.name, 
                                              host_is_bot=True, 
                                              guest=os.environ.get('USER') or os.environ.get('USERNAME'), 
                                              guest_is_bot=False)
        
        collection=self.chroma_handler.chroma_get_or_create_collection(f"{agent.name}-{conversation.guest}")

        # Instantiate the server, find an available port, and start the server on that port. 
        server = OllamaServer()
        server.find_available_port()
        print(f"This session will use port: {server.port}")
        server.start_server()

        try:
            while True:
                # Get the user's request
                request = input("User>> ")

                if request == 'exit' or request == 'quit':   # Check if the user wants to exit
                    print("Exiting chat...\n\n")
                    break
                elif request == '!focus':
                    input(f"Current focus: {agent.instructions.assistant_focus}. Type a new focus message or press enter to keep this one.")
                    if input == '':
                        continue
                    else:
                        agent.instructions.assistant_focus = input
                        continue
                
                # Convert to Message class
                request_message = Message(
                    uuid=str(uuid4()),
                    timestamp=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
                    role='user',
                    speaker=conversation.guest,
                    content=request
                )

                # Build the prompt
                username = os.environ.get('USER') or os.environ.get('USERNAME')
                prompt = agent.build_prompt(request_message.content, username=username, agent_agent=False)

                #####  DEBUG: PROMPT  #####
                debug_print_function_return('Prompt', prompt)
                #####  DEBUG END  #####

                # Get the response and stream it to the terminal
                response_content = agent.generate_response(prompt=prompt, server_port=server.port)

                # Convert response to message class and pull the message string
                response_message = Message(
                    uuid=str(uuid4()),
                    timestamp=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
                    role='assistant',
                    speaker=conversation.host,
                    content=response_content
                )

                stream_agent_response(agent.name, text=response_content, delay=.05)

                # Create turn and add to chat history
                convo_turn = Turn(
                    uuid=str(uuid4()),
                    request=request_message,
                    response=response_message
                )

                agent.message_cache.add_message(convo_turn)

                # Chroma Upsert
                document = convo_turn.request.to_memory_string()
                document += convo_turn.response.to_memory_string()
                #print(f"Documents: {document}")
                self.chroma_handler.chroma_upsert_to_collection(collection=collection, metadata=None, document=document, id=convo_turn.uuid)
                

                ###  DEBUG: TURN BASE DICT  ###
                #debug_print_function_return('Turn Base Dict', convo_turn.to_dict())
                ###  DEBUG END  ###

                # Add Turn to Conversation YAML
        except KeyboardInterrupt:
            print("Interrupted by user...\n")
        
        finally:
            print("Chat session ended.")
            server.stop_server()


    def multi_agent_chat(self, host_agent_name: str, guest_agent_name: str) -> None:
        """
        Puts two agents into a chat session together. Super fun. Warning: This function uses exec through the OllamaServer instance to find available ports and start a server on that port. The server is stopped when the chat session ends.

        :param host_agent: The name of the agent to host the chat.
        :param guest_agent: The name of the agent to join the chat.
        :returns: Hours of enjoyment if you know how to prompt..
        """
        # Load the host agent from file
        host_agent_model_instructions = ModelInstructions(method='load', assistant_name=host_agent_name)
        host_agent_params_config = ParamsConfig(method='load', assistant_name=host_agent_name)
        host_agent = Agent(host_agent_params_config, host_agent_model_instructions)
        # Load the guest agent from file
        guest_agent_model_instructions = ModelInstructions(method='load', assistant_name=guest_agent_name)
        guest_agent_params_config = ParamsConfig(method='load', assistant_name=guest_agent_name)
        guest_agent = Agent(guest_agent_params_config, guest_agent_model_instructions)

        # Print the banners
        toilet_banner_metal(host_agent.name)
        toilet_banner_plain('welcomes')
        toilet_banner_metal(guest_agent.name)

        # Start a new conversation for chat logging. TODO: ability to check existing conversations and load OR new
        conversation = start_new_conversation(host_agent, 
                                              host_is_bot=True, 
                                              guest=guest_agent, 
                                              guest_is_bot=True)
        
        server = OllamaServer()
        server.find_available_port()
        print(f"This session will use port: {server.port}")
        server.start_server()
        
        host_collection = self.chroma_handler.chroma_get_or_create_collection(f"{host_agent.name}-{guest_agent.name}")
        guest_collection = self.chroma_handler.chroma_get_or_create_collection(f"{guest_agent.name}-{host_agent.name}")


        # Get the guest's first message before entering the chat to give the while loop a little better progression.
        host_agent.last_response = f"Hello, I'm {host_agent.name}, welcome to my room! People describe me as: {host_agent.instructions.description}. Please first tell me a little bit about yourself, and then give me 2 topics that you may be interested in speaking with me about. As your host, I will choose our first subject from your list."

        try:
            while True:
                guest_prompt = guest_agent.build_prompt(host_agent.last_response, username=host_agent.name, agent_agent=True)
                debug_print_function_return('Guest Prompt', guest_prompt)
                guest_agent.last_response = guest_agent.generate_response(prompt=guest_prompt, server_port=server.port)

                guest_request_message = Message(
                    uuid=str(uuid4()),
                    timestamp=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
                    role='user',
                    speaker=guest_agent.name,
                    content=guest_agent.last_response
                )

                # Stream the guest request to the terminal chat
                stream_agent_response(guest_agent.name, guest_agent.last_response, 0.05)
                
                # Request to Hosting Agent
                host_agent_prompt = host_agent.build_prompt(guest_agent.last_response, username=guest_agent.name, agent_agent=True)
                debug_print_function_return('Host Prompt', host_agent_prompt)
                host_agent.last_response = host_agent.generate_response(prompt=host_agent_prompt, server_port=server.port)

                host_response_message = Message(
                    uuid=str(uuid4()),
                    timestamp=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
                    role='assistant',
                    speaker=host_agent.name,
                    content=host_agent.last_response
                )

                # Stream the host response to the terminal chat
                stream_agent_response(host_agent.name, host_agent.last_response, 0.05)

                # Create turn and add to chat history
                message_turn = Turn(
                    uuid=str(uuid4()),
                    request=guest_request_message,
                    response=host_response_message
                )

                # Add Turn to each agents' message cache for prompt context
                host_agent.message_cache.add_message(message_turn)
                guest_agent.message_cache.add_message(message_turn)

                # Add Turn to Conversation
                conversation.create_turn(guest_request_message, host_response_message)
                document = message_turn.request.to_memory_string()
                document += message_turn.response.to_memory_string()
                self.chroma_handler.chroma_upsert_to_collection(collection=host_collection, metadata=None, document=document, id=message_turn.uuid)
                self.chroma_handler.chroma_upsert_to_collection(collection=guest_collection, metadata=None, document=document, id=message_turn.uuid)
        except KeyboardInterrupt:
            print("Interrupted by user...\n")
        
        finally:
            print("Chat session ended.")
            server.stop_server()
