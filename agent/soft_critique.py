from llm import BaseLLM
from .abstract import BaseAgent
from .agent_utils import extract_judgement


class SoftCritiqueAgent(BaseAgent):
    description = 'Soft critique of autoformalization from LLMs.'

    def __init__(self,
                 llm: BaseLLM,
                 name: str = 'SoftCritiqueAgent',
                 formal_language: str = 'Isabelle/HOL',
                 aspect_description: str = ''):
        super().__init__(name=name)

        basic_system_prompt = (
            'You are an expert in formal language {formal_language}.\n'
            'You will be given a mathematical statement written in natural language and LaTeX symbols.\n'
            'You will also be given a formal code which attempted to describe the given mathematical '
            'statement in {formal_language}.\n'
            'Your task is to evaluate a specific aspect of the formal code.\n'
            'The description of the aspect is: {{aspect_description}}\n'
            'Your need to give two things about your evaluation:\n'
            '1. the judgement of whether the formalization meets this aspect. '
            'This should be a binary value in \"True\" or \"False\".\n'
            '2. the detailed explanation of your judgement.\n'
            'You should wrap your final results in a way illustrated as the following:\n'
            '%%%%%%%%%%\n'
            'Explanation: Your Detailed Explanation\n'
            'Judgement: Your Binary Judgement\n'
            '%%%%%%%%%%\n'
            'Strictly follow the instructions that have been claimed.\n'
        )

        user_prompt = (
            'Natural language statement: {{informal_statement}}\n'
            '{formal_language} formal code of the statement: {{formalization}}\n'
        )

        placeholder = {'informal': '{informal_statement}',
                       'formalization': '{formalization}'}

        self.llm = llm

        self.formal_language = formal_language
        self.system_prompt = basic_system_prompt
        self.system_prompt = self.system_prompt.replace(
            '{formal_language}', self.formal_language)
        self.system_prompt = self.system_prompt.replace('{aspect_description}', aspect_description)
        self.user_prompt = user_prompt.replace(
            '{formal_language}', self.formal_language)
        self.placeholder = placeholder

    def get_messages(self,
                     informal_statement: str = '',
                     formalization: str = ''):
        messages = [{'role': 'system', 'content': self.system_prompt}]
        user_content = self.user_prompt.replace(
            self.placeholder['informal'], informal_statement)
        user_content = user_content.replace(
            self.placeholder['formalization'], formalization)
        messages.append({'role': 'user', 'content': user_content})
        return messages

    def _agent_function(self,
                        informal_statement: str = '',
                        formalization: str = ''):
        messages = self.get_messages(informal_statement=informal_statement,
                                     formalization=formalization)
        response = self.llm.generate(messages)
        return extract_judgement(response), response
