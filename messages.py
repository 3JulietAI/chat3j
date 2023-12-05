from dataclasses import dataclass, asdict, field
from datetime import datetime
from uuid import uuid4
from typing import List
from collections import deque
import yaml


@dataclass
class Message:
    uuid: str
    role: str
    speaker: str
    content: str
    timestamp: str = str(datetime.now().strftime('%Y-%m-%d @ %H:%M'))
    
    def to_dict(self):
        """
        Exports the Message container to an iterable

        :param self: The message instance to convert
        :return: dict representation
        """
        
        return asdict(self)

    def dep_to_chat_history_dict(self):
        """
        *DEPRECATED*
        Exports the Message container to a dictionary specifically for inclusion in chat history.

        :param self:
        :return: dict
        """
        chat_history_dict = {
            "role": self.role,
            "content": self.content,
        }
        
        return chat_history_dict

    def to_prompt_message_string(self):
        """
        Converts a Message object to a string that can be sent to the model.

        :param message: The Message object to convert.
        :return: A string that can be sent to the model.
        """
        return f"<|im_start|>{self.speaker}: \n{self.content}<|im_end|>"
    
    def to_memory_string(self):
        """
        Converts a Message object to a string more suitable for context recall.

        :param message: The Message object to convert.
        :return: A string that can be sent to the model.
        """
        return f"{self.speaker} @ {self.timestamp}: {self.content}"


@dataclass
class Turn:
    uuid: str
    request: Message
    response: Message

    def dep_to_dict(self):
        """
        *DEPRECATED*
        Converts the Turn dataclass instance to a dictionary.
        """
        return {
            #"conversation": self.conversation,
            "uuid": self.uuid,
            "request": self.request,
            "response": self.response,
        }

    def to_dict(self):
        """
        Converts the Turn dataclass instance to a dictionary.
        """
        return asdict(self)


@dataclass
class Conversation:
    uuid: str
    created_at: str
    last_active: str
    host: str
    host_is_bot: bool
    guest: str
    guest_is_bot: bool
    turns: List[Turn] = field(default_factory=list)

    def to_dict_dep(self):
        return {
            "uuid": self.uuid,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "host": self.host,
            "host_is_bot": self.host_is_bot,
            "guest": self.guest,
            "guest_is_bot": self.guest_is_bot,
            "turns": [turn.to_dict() for turn in self.turns],
        }

    def to_dict(self):
        return asdict(self)
    
    def create_turn(self, request: Message, response: Message) -> Turn:
        """
        Creates a new MessageTurn object.

        :param request: The request Message object.
        :param response: The response Message object.

        :return: A MessageTurn object.
        """
        return Turn(
            uuid=str(uuid4()),
            request=request,
            response=response
        )


@dataclass
class MessageCache:
    """
    This class manages the conversation history for inclusion in prompt context injection as a deque with structural
    preservation on i/o
    """

    def __init__(self, capacity, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.capacity = capacity
        self.cache = deque(maxlen=capacity)

    def add_message(self, turn: Turn):
        self.cache.append(turn)

    def get_message_cache(self):
        message_cache = list(self.cache)
        return message_cache
    
    def get_n_messages(self, n):
        message_cache = list(self.cache)[-n:]
        return message_cache
    
    def get_chat_history(self):
        chat_history = []
        for turn in self.cache:
            chat_history.append(turn.request.to_prompt_message_string())
            chat_history.append(turn.response.to_prompt_message_string())
        return chat_history


def start_new_conversation(host: str, host_is_bot: bool, guest: str, guest_is_bot: bool) -> Conversation:
    """
    Starts a new conversation and returns the conversation UUID.

    :param host: The name of the host
    :param host_is_bot: Whether the host is a bot
    :param guest: The name of the guest agent
    :param guest_is_bot: Whether the guest is a bot

    :return: Conversation object
    """
    conversation = Conversation(
        uuid=str(uuid4()),
        created_at=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
        last_active=str(datetime.now().strftime('%Y-%m-%d @ %H:%M')),
        host=host,
        host_is_bot=host_is_bot,
        guest=guest,
        guest_is_bot=guest_is_bot,
        turns=[]
    )
    
    print(f"New conversation {conversation.uuid} started!")

    return conversation


def append_turn_to_conversation_yaml(conversations_file_path: str, conversation_uuid: str, turn: Turn) -> None:
    # TODO: testing
    """
    Appends a turn to the specified conversation in the YAML file.

    :param conversation_file_path: The file path of the YAML file.
    :param conversation_uuid: The UUID of the conversation to append to.
    :param turn: The turn data to append.
    """
    turn_dict = turn.to_dict()
    # Load the existing conversations
    with open(conversations_file_path, 'r') as file:
        data = yaml.safe_load(file) or {"conversations": []}

    # Find the conversation by UUID
    conversation = next((c for c in data["conversations"] if c["uuid"] == conversation_uuid), None)
    
    if conversation:
        # Append the new turn and update last_active
        conversation["turns"].append(turn_dict)
        conversation["last_active"] = turn_dict["response"]["timestamp"]
    else:
        # If the conversation wasn't found, create a new one and append the turn
        conversation = {
            "uuid": conversation_uuid,
            "created_at": turn_dict["request"]["timestamp"],
            "last_active": turn_dict["response"]["timestamp"],
            "turns": [turn_dict]
        }
        data["conversations"].append(conversation)
    
    # Write the updated list of conversations back to the YAML file
    with open(conversations_file_path, 'w') as file:
        yaml.safe_dump(data, file)


def format_chat_history(chat_history: list):
    """
    Formats the chat history for display.
    """
    # Join the strings in the list
    formatted_history = ''.join(chat_history)
    
    # Optional: Replace consecutive newlines with a single newline
    formatted_history = formatted_history.replace('\n\n', '\n')

    return formatted_history


def split_corpus_into_chunks(corpus, chunk_size=100, overlap=50):
    tokens = corpus.split()
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunks.append(' '.join(tokens[start:end]))
        start += (chunk_size - overlap)

    return chunks


