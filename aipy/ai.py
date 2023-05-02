import openai
import os

DEFAULT_QUESTION = 'Describe the purpose and algorithm for this code'
DEFAULT_MODEL = 'gpt-3.5-turbo'

def gptchat(messages, max_tokens):
    completions = openai.ChatCompletion.create(
        model=DEFAULT_MODEL, messages=messages, max_tokens=max_tokens,
        temperature=0.2)
    print(completions['choices'][0]['message']['content'])
    return completions


def describe_code(code_path, question=DEFAULT_QUESTION, max_tokens=2000):
    lang_map = {'py': 'Python', 'R': 'R'}
    language = lang_map[os.path.splitext(code_path)[1][1:]]
    with open(code_path) as file:
        code = file.read()
    messages=[
        {"role": "system", "content": f'You are an expert in the {language} language.'},
        {"role": "user", "content": f"{question}: {code}"},
    ]
    completions = gptchat(messages, max_tokens)
    return completions


def ask_gpt(question, max_tokens = 2000):
    messages=[
        {"role": "system", "content": 'You are wise and helpful.'},
        {"role": "user", "content": question},
    ]
    completions = gptchat(messages, max_tokens)
    return completions
