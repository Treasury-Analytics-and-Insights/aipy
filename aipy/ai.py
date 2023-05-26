import datetime
import json
import os
import pickle

import openai


DEFAULT_MODEL = 'gpt-3.5-turbo'

class Chat(object):
    def __init__(self, messages=None) -> None:
        if messages is None:
            self.messages = messages=[
                {"role": "system", "content": 'You are wise and helpful.'}]
        else:
            self.messages = messages
        
    def ask(self, question, max_tokens=2000, model=DEFAULT_MODEL, temperature=1, keep=True) -> None:
        messages = self.messages + [{"role": "user", "content": question}]
        completions = openai.ChatCompletion.create(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature)
        answer = completions['choices'][0]['message']['content']
        messages.append({"role":"assistant", "content": answer})
        if keep:
            self.messages = messages
        return answer
    
    def get_topics(self) -> list:
        a = self.ask(
            'Give me up to three descriptive one word topics for this chat, in a JSON list, with no introduction or explanation', 
            max_tokens=40, keep=False)
        return json.loads(a[a.index('['):a.index(']')+1])

    def suggest_filename(self):
        topics = self.get_topics()

        filename = f"{'_'.join(topics)}_{datetime.datetime.now().strftime('%y%m%d_%H%M%S')}.pkl"

        return filename

    def save(self, path=None, directory='.'):
        if path is None:
            path = os.path.join(directory, self.suggest_filename())
        with open(path, 'wb') as f:
            print(f'Saving Chat object to {path}')
            pickle.dump(self.messages, f)


class CodeInspector(Chat):
    lang_map = {'py': 'Python', 'R': 'R'}
 
    def __init__(self, code_path) -> None:
        language = CodeInspector.lang_map[os.path.splitext(code_path)[1][1:]]
        with open(code_path) as f:
            self.code_path = code_path
            self.code = f.read()
        self.messages=[
            {"role": "system", "content": f'You are an expert in the {language} language.'},
            {"role": "user", "content": f"Here is some code I want to ask questions about: {self.code}"}]   

    def ask(self, question, temperature=0.2):
        super().ask(question, temperature=temperature)

    def describe(self, temperature=0.2):
        self.ask('Describe the purpose and algorithm for this code', temperature=temperature)


def load_chat(path):
    with open(path, 'rb') as f:
        return Chat(pickle.load(f))