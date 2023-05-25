import openai
import os

DEFAULT_MODEL = 'gpt-3.5-turbo'

class Chat(object):
    def __init__(self) -> None:
        self.messages = messages=[
            {"role": "system", "content": 'You are wise and helpful.'}]
        
    def ask(self, question, max_tokens=2000, model=DEFAULT_MODEL, temperature=1):
        messages = self.messages + [{"role": "user", "content": question}]
        completions = openai.ChatCompletion.create(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature)
        answer = completions['choices'][0]['message']['content']
        messages.append({"role":"assistant", "content": answer})
        self.messages = messages
        return completions


class CodeInspector(Chat):
    lang_map = {'py': 'Python', 'R': 'R'}
 
    def __init__(self, code_path) -> None:
        language = CodeInspector.lang_map[os.path.splitext(code_path)[1][1:]]
        with open(code_path) as file:
            self.code_path = code_path
            self.code = file.read()
        self.messages=[
            {"role": "system", "content": f'You are an expert in the {language} language.'},
            {"role": "user", "content": f"Here is some code I want to ask questions about: {self.code}"}]   

    def ask(self, question, temperature=0.2):
        return super().ask(question, temperature=temperature)

    def describe(self, temperature=0.2):
        self.ask('Describe the purpose and algorithm for this code', temperature=temperature)
