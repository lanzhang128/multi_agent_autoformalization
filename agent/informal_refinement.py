from llm import BaseLLM
from .abstract import BaseAgent
from .agent_utils import extract_formal_code


class InformalRefinementAgent(BaseAgent):
    description = 'LLM Agent for refining autoformalization codes with feedback from LLMs.'

    def __init__(self,
                 llm: BaseLLM,
                 name: str = 'FormalRefinementAgent',
                 formal_language: str = 'Isabelle/HOL'):
        super().__init__(name=name)

        basic_system_prompt = (
            'You are an expert in formal language {formal_language}.\n'
            'You will be given a mathematical statement written in natural language and LaTeX symbols.\n'
            'You will also be given a formal code which attempted to describe the given mathematical '
            'statement in {formal_language}.\n'
            'Your task is to refine the given formal code to make it satisfy a specific aspect while '
            'maintaining the alignment with the given natural language mathematical statement.\n'
            'Here are some instructions for your task:\n'
            '1. You should give the formal code directly without any additional explanation or any proof.\n'
            '2. In case that you need to import any necessary preambles, you should not import '
            'any fake (non-exist) preambles.\n'
            '3. You should wrap the formal code in a way illustrated as the following:\n'
            '%%%%%%%%%%\n'
            'Your Formal Code\n'
            '%%%%%%%%%%\n'
            'Strictly follow the instructions that have been claimed.\n'
        )

        user_prompt = (
            'Natural language statement: {{informal_statement}}\n'
            'There are some {formal_language} formal codes describing the given mathematical '
            'statement: {{formalization}}\n'
            'You should refine this piece of code for your task.\n'
            'The description of the aspect which you should focus on is: {{aspect_description}}\n'
            'The result of the evaluation of this aspect is: {{aspect_evaluation}}\n'
        )

        placeholder = {'informal': '{informal_statement}',
                       'formalization': '{formalization}',
                       'aspect_description': '{aspect_description}',
                       'aspect_evaluation': '{aspect_evaluation}'}

        self.llm = llm

        self.formal_language = formal_language
        self.system_prompt = basic_system_prompt.replace(
            '{formal_language}', self.formal_language)
        self.user_prompt = user_prompt.replace(
            '{formal_language}', self.formal_language)
        self.placeholder = placeholder

    def get_messages(self,
                     informal_statement: str = '',
                     formalization: str = '',
                     aspect_description: str = '',
                     aspect_evaluation: str = ''):
        messages = [{'role': 'system', 'content': self.system_prompt}]
        user_content = self.user_prompt.replace(
            self.placeholder['informal'], informal_statement)
        user_content = user_content.replace(
            self.placeholder['formalization'], formalization)
        user_content = user_content.replace(
            self.placeholder['aspect_description'], aspect_description)
        user_content = user_content.replace(
            self.placeholder['aspect_evaluation'], aspect_evaluation)
        messages.append({'role': 'user', 'content': user_content})
        return messages

    def _agent_function(self,
                        informal_statement: str = '',
                        formalization: str = '',
                        aspect_description: str = '',
                        aspect_evaluation: str = ''):
        messages = self.get_messages(informal_statement=informal_statement,
                                     formalization=formalization,
                                     aspect_description=aspect_description,
                                     aspect_evaluation=aspect_evaluation)
        response = self.llm.generate(messages)
        return extract_formal_code(response), response
