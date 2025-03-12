from llm import BaseLLM
from .abstract import BaseAgent
from .agent_utils import get_postprocess_fn


class DenoisingAgent(BaseAgent):
    description = 'Agent for cleaning output of LLMs to get autoformalization codes.'

    def __init__(self,
                 llm: BaseLLM,
                 name: str = 'DenoisingAgent',
                 formal_language: str = 'Isabelle/HOL'):
        super().__init__(name=name)

        basic_system_prompt = (
            'You are an expert in formal language {formal_language}.\n'
            'You will be provided a piece of text containing {formal_language} code.\n'
            'Your task is to obtain cleaned {formal_language} code from the provided text with '
            'the following instructions:\n'
            '1. You should obtain the cleaned code only from the provided text. '
            'Do not attempt to rewrite or improve the cleaned code.\n'
            '2. You should only output the cleaned code directly. '
            'Anything else, including but not limited to note, description, explanation and comment, '
            'must be removed from the final answer. Giving any additional text is also prohibited.\n'
            '3. The provide text might contain several repeated or similar formal statements. '
            'The cleaned code must only keep the best one among them.\n'
            '4. Do not have any proof in the cleaned code. '
            'If there are proofs in the provided text, remove it from the cleaned code.\n'
            'Strictly follow the instructions that have been claimed.\n'
            'You should wrap the cleaned formal code in a way that is illustrated as the following:\n'
            '%%%%%%%%%%\n'
            'Your Formal Code\n'
            '%%%%%%%%%%\n'
        )

        additional_system_prompt = ''

        user_prompt = (
            'There are some texts containing autoformalized {formal_language} codes: {{formalization}}\n'
            'Clean them to obtain cleaned {formal_language} code.\n'
        )

        placeholder = {'formalization': '{formalization}'}

        self.llm = llm
        self.postprocess_fn = get_postprocess_fn(self.llm)

        self.formal_language = formal_language
        self.system_prompt = basic_system_prompt + additional_system_prompt
        self.system_prompt = self.system_prompt.replace(
            '{formal_language}', self.formal_language)
        self.user_prompt = user_prompt.replace(
            '{formal_language}', self.formal_language)
        self.placeholder = placeholder

    def get_messages(self,
                     formalization: str = ''):
        messages = [{'role': 'system', 'content': self.system_prompt}]
        user_content = self.user_prompt.replace(
            self.placeholder['formalization'], formalization)
        messages.append({'role': 'user', 'content': user_content})
        return messages

    def _agent_function(self,
                        formalization: str = ''):
        messages = self.get_messages(formalization=formalization)
        response = self.llm.generate(messages)
        return self.postprocess_fn(response), response
