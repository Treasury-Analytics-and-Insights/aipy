"""
This module provides classes for managing chat logs and code inspection.

Classes:
- Chat: Represents a chat log and provides methods for interacting with OpenAI's GPT-3 API.
- CodeInspector: Represents a code file and provides methods for asking questions about the code.
- ChatDB: Represents a database of chat logs and provides methods for storing and searching logs.

Methods:
- load_chat(path): Loads a Chat object from a pickle file at the given path.
"""

from collections import namedtuple
import datetime
import json
import os
import pickle

import openai
from prettytable import PrettyTable
import tinydb 

DEFAULT_MODEL = 'gpt-3.5-turbo'

ChatDoc = namedtuple('ChatDoc',['name', 'date', 'topics', 'summary', 'messages'])


class Chat(object):
    """
    Represents a chat log and provides methods for interacting with OpenAI's GPT-3 API.

    Attributes:
    - messages: A list of dictionaries representing the chat messages, 
    with each dictionary containing 'role' and 'content' keys.
    """
    print_from = 0
    def __init__(self, messages=None, topics=None, summary=None) -> None:
        """Initializes a new Chat object with the given messages, 
        or a default message if none are provided."""

        if messages is None:
            self.messages = messages=[
                {"role": "system", "content": 'You are wise and helpful.'}]
        else:
            self.messages = messages
        self.topics = topics
        self.summary = summary

    def add_context(self, context):
        """Add context to the chat - chatgpt is not called"""
        self.messages.append({"role": "user", "content": context}) 

    def ask(self, question, max_tokens=2000, model=DEFAULT_MODEL, temperature=1, keep=True) -> str:
        """Sends a message to the GPT-3 API and returns the response.  
        By default append the prompt and response to the chat history""" 

        messages = self.messages + [{"role": "user", "content": question}]
        completions = openai.ChatCompletion.create(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature)
        answer = completions['choices'][0]['message']['content']
        messages.append({"role":"assistant", "content": answer})
        if keep:
            self.messages = messages
        return answer
    
    def get_topics(self, model) -> list:
        """Asks the chatgpt to provide up to three descriptive topics for the chat and returns them as a list."""
        a = self.ask(
            'Give me up to three descriptive one word topics for this chat, in a JSON list, '
            'with no introduction or explanation.  It is important that you use square brackets '
            'to format the list so that I can parse the output', 
            max_tokens=40, model=model, keep=False, temperature = 0.2)
        self.topics = json.loads(a[a.index('['):a.index(']')+1])

    def get_summary(self, model=DEFAULT_MODEL):
        """Asks the chatgpt to describe the chat in one sentence and returns the response."""
        self.summary = self.ask('Describe this chat in one sentence', model=model, max_tokens=200, keep=False)
        return self.summary

    def format(self) -> str:
        """Format the conversation text"""
        txt = '\n\n-----------------------------------------\n\n'.join(
            [msg['content'] for msg in self.messages[self.print_from:]])
        return txt

    def print(self) -> None:
        "print formatted text of the conversation to screen"
        print(self.format())

    def write_txt(self, path=None, directory='.', model = DEFAULT_MODEL):
        "write formatted text of the converstaion to file"
        if path is None:
            if self.topics is None:
                print("No path specified, attempting to determine topic and filename")
                self.get_topics(model)
            path = os.path.join(directory, f"{'_'.join(self.topics)}_chat.txt")

        txt = self.format()        
        with open(path, 'w', encoding="utf8") as f:
            f.write(txt)

        print(f'Saved chat log to {path}')

    def to_db_doc(self, model=DEFAULT_MODEL) -> ChatDoc:
        if self.topics is None:
            self.get_topics(model)
        if self.summary is None:
            self.get_summary(model)
        
        date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = '-'.join([topic.replace(' ' , '_') for topic in self.topics]+[date])

        return ChatDoc(name, date, self.topics, self.summary, self.messages)._asdict()
    
    @staticmethod
    def from_db_doc(doc:ChatDoc):
        return Chat(messages=doc.messages, topics=doc.topics, summary=doc.summary)



class CodeInspector(Chat):
    """Subclass of Chat for inspecting a source code file"""
    lang_map = {'py': 'Python', 'R': 'R'}
    print_from = 2
 
    def __init__(self, code_path) -> None:
        language = CodeInspector.lang_map[os.path.splitext(code_path)[1][1:]]
        with open(code_path) as f:
            self.code_path = code_path
            self.code = f.read()
        self.messages=[
            {"role": "system", "content": f'You are an expert in the {language} language.'}]
        
        self.add_context(f"Here is some code I want to ask questions about: {self.code}")
        self.topics = None
        self.summary = None   


    def describe(self, temperature=0.2, model=DEFAULT_MODEL):
        self.ask('Describe the purpose and algorithm for this code', temperature=temperature, model=model)


class ChatDB(object):
    """
    Represents a database of chat logs and provides methods for storing and searching logs.

    Attributes:
    - db: A TinyDB object representing the database.

    Methods:
    - __init__(path=None): Initializes a new ChatDB object with the database at the given path, or a default path if none is provided.
    - store(chat): Stores the given Chat object in the database.
    - summarise(): Prints a summary of all chats in the database to the console and returns a PrettyTable object.
    - search(query): Searches the database for chats matching the given query and returns a list of Chat objects.
    - close(): Closes the database connection.
    """
        
    default_filename = 'chats.json'
    
    def __init__(self, path = None) -> None:
        """
        Initializes a new ChatDB object with the database at the given path, or a default path if none is provided.

        Args:
        - path: The path to the database.
        """
        if path is None:
            onedrive_path = os.getenv('OneDrive')
            path = os.path.join(
                {True:'./', False:onedrive_path}[onedrive_path is None], 
                ChatDB.default_filename)
        self.path = path
        print(f"Opening chat database: {path}")
        self.db = tinydb.TinyDB(path)

    def store(self, chat: Chat, model=DEFAULT_MODEL) -> None:
        """
        Stores the given Chat object in the database.

        Args:
        - chat: The Chat object to store.
        """
        self.db.insert(chat.to_db_doc(model))

    def summarise(self) -> PrettyTable:
        """
        Prints a summary of all chats in the database to the console and returns a PrettyTable object.

        Returns:
        - A PrettyTable object representing the summary of all chats in the database.
        """
        table = PrettyTable()
        table.field_names = ['Name', 'Date', 'Topics', 'Summary']
        for doc in self.db:
            table.add_row([doc[k] for k in ['name', 'date', 'topics', 'summary']])
        print(table)
        return table
    
    def search(self, query) -> list:
        """
        Searches the database for chats matching the given query and returns a list of Chat objects.

        Args:
        - query: The query to search for.

        Returns:
        - A list of Chat objects matching the query.
        """
        matches = self.db.search(query)
        return [Chat.from_db_doc(ChatDoc(**doc)) for doc in matches]
    
    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.db.close()

