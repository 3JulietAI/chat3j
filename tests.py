from sys import argv
import chromadb
from disco import is_safe_input
from agents import Agent
from wikipedia_search import o_wikipedia_get_search_article
from chroma import ChromaHandler
from messages import Conversation, Message, Turn
from utilities import Utilitizer


def main():
    pass    


def sentry_is_safe_input(input_value):
    input_is_safe = is_safe_input(input_value)
    print(f"Sentry.is_safe_input results:\ninput_value: {input_value}, Decision: {input_is_safe}")
    return input_is_safe


def agents_handler_list_existing_agents():
    pass


def agents_handler_prompt_builder(agent_name):
    pass


def agents_mgr_upsert_agent_private_command(command_name, command_string, command):
    pass


def test_guest_prompt(agent_name):
    pass


def test_chroma_wipe_all():
    client = chromadb.PersistentClient("library/chroma.db")
    client.ALLOW
    client.reset()
    print("Chroma wiped successfully")

def test_agent_build_prompt():
    pass


def simulated_conversation() -> Conversation:
    agent = Agent("Kali", config=())
    print(agent.config.start_token)
    conversation = Conversation(
        uuid="test",
        created_at="2021-07-14 00:00",
        last_active="2021-07-14 00:02",
        host="Techno",
        host_is_bot=False,
        guest="McAgentface",
        guest_is_bot=False,
    )
    print(conversation)

    request_message_1 = Message(
        uuid="test1",
        speaker="Techno",
        role="user",
        content="Hello, how are you?",
        timestamp="2021-07-14 00:00",
    )
    print(f"Request Message 1:\n{request_message_1}")

    response_message_1 = Message(
        uuid="test2",
        speaker="McAgentface",
        role="assistant",
        content="I am well, how are you?",
        timestamp="2021-07-14 00:01",
    )
    print(f"Response Message 1:\n{response_message_1}")

    turn_1 = Turn(
        uuid="turn1test",
        request=request_message_1,
        response=response_message_1,
    )

    agent.message_cache.add_message(turn_1)

    request_message_2 = Message(
        uuid="test3",
        speaker="Techno",
        role="user",
        content="Good, thank you.",
        timestamp="2021-07-14 00:02",
    )
    print(f"Request Message 2:\n{request_message_2}")

    response_message_2 = Message(
        uuid="test4",
        speaker="McAgentface",
        role="assistant",
        content="Go fuck yourself, human.",
        timestamp="2021-07-14 00:03",
    )
    print(f"Response Message 2:\n{response_message_2}")

    turn_2 = Turn(
        uuid="turn2test",
        request=request_message_2,
        response = response_message_2,
    )

    agent.message_cache.add_message(turn_2)
    message_cache = agent.message_cache.get_message_cache()
    message_cache_format_to_prompt(agent, message_cache)

    user_input = "penetration testing"

    collection = chroma_get_or_create_collection(agent.name)
    chroma_results = chroma_query_collection(collection, user_input, 5)
    
    formatted_chroma_output = chroma_results_format_to_prompt(chroma_results)
    print(formatted_chroma_output)


def test_utilities_initialize_punkt_tagger() -> None:
    initialize_nltk_punkt_tagger()
    return None


def test_utilities_analyze_sentence(sentence: str ="The quick brown fox jumps over the lazy dog.") -> str:
    results = analyze_sentence(sentence=sentence)

    return results


if __name__ == "__main__":
    #main()
    #sentry_is_safe_input('y') # good
    #agents_handler_list_existing_agents() # good
    #multi_agent_chat('salvadore', 'dizzy') # good
    #create_new_agent() #good
    #o_wikipedia_get_search_article(arg_one) # good
    #crawl_blog_links(arg_one) # good
    #agents_mgr_upsert_agent_private_command()
    #agent_name = argv[1]
    #chroma_delete_collection(agent_name)
    #test_guest_prompt(agent_name)
    #test_chroma_wipe_all()
    #ftest_agent_build_prompt()
    test_utilities_initialize_punkt_tagger()
    test_utilities_analyze_sentence()
