from typing import Optional, List

from llm import BaseLLM
from .abstract import BaseAgent
from .agent_utils import get_postprocess_fn


class AutoformalizationAgent(BaseAgent):
    description = 'Agent for zero-shot and few-shot autoformalization with LLMs.'

    def __init__(self,
                 llm: BaseLLM,
                 name: str = 'AutoformalizationAgent',
                 formal_language: str = 'Isabelle/HOL'):
        super().__init__(name=name)

        basic_system_prompt = (
            'You are an expert in formal language {formal_language}.\n'
            'Your task is to provide the formal code of the given natural language '
            'mathematical statement in {formal_language}.\n'
            'In case that you need to import any necessary preambles, '
            'you should not import any fake (non-exist) preambles.\n'
            'You should wrap the formal code in a way illustrated as the following:\n'
            '%%%%%%%%%%\n'
            'Your Formal Code\n'
            '%%%%%%%%%%\n'
        )

        additional_system_prompt = ''

        user_prompt = (
            'Give the {formal_language} formal code of the following natural language statement:\n'
            '{{informal_statement}}\n'
            'directly without any additional explanations and do not give any proof.\n'
        )
        assistant_prompt = '{formal_statement}'

        placeholder = {
            'informal': '{informal_statement}',
            'formal': '{formal_statement}'
        }

        self.llm = llm
        self.postprocess_fn = get_postprocess_fn(self.llm)

        self.formal_language = formal_language
        self.system_prompt = basic_system_prompt + additional_system_prompt
        self.system_prompt = self.system_prompt.replace(
            '{formal_language}', self.formal_language)
        self.user_prompt = user_prompt.replace(
            '{formal_language}', self.formal_language)
        self.assistant_prompt = assistant_prompt
        self.placeholder = placeholder

    def get_messages(self,
                     informal_statement: str = '',
                     informal_formal_pairs: Optional[List[List[str]]] = None):
        messages = [{'role': 'system', 'content': self.system_prompt}]
        if informal_formal_pairs is not None:
            for informal, formal in informal_formal_pairs:
                messages.append(
                    {'role': 'user',
                     'content': self.user_prompt.replace(
                         self.placeholder['informal'], informal)})
                messages.append(
                    {'role': 'assistant',
                     'content': self.assistant_prompt.replace(
                         self.placeholder['formal'], formal)}
                )
        user_content = self.user_prompt.replace(
            self.placeholder['informal'], informal_statement)
        messages.append({'role': 'user', 'content': user_content})
        return messages

    def _agent_function(self,
                        informal_statement,
                        informal_formal_pairs: Optional[List[List[str]]] = None):
        messages = self.get_messages(informal_statement=informal_statement,
                                     informal_formal_pairs=informal_formal_pairs)
        response = self.llm.generate(messages)
        return self.postprocess_fn(response), response
