from chroma import ChromaHandler
from sys import argv


def main():
    agent_name = argv[1]
    ChromaHandler.chroma_delete_collection(agent_name)
    print(f"Deleted collection for {agent_name}.")