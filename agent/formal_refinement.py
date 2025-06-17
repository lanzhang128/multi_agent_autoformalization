from typing import Optional

from llm import BaseLLM
from .abstract import BaseAgent
from .agent_utils import extract_formal_code


class FormalRefinementAgent(BaseAgent):
    description = 'LLM Agent for refining autoformalization codes with error feedback from theorem prover.'

    def __init__(self,
                 llm: BaseLLM,
                 name: str = 'FormalRefinementAgent',
                 formal_language: str = 'Isabelle/HOL',
                 category: str = 'none'):
        super().__init__(name=name)

        basic_system_prompt = (
            'You are an expert in formal language {formal_language}.\n'
            'You will be given a mathematical statement written in natural language and LaTeX symbols.\n'
            'You will also be given a formal code which attempted to describe the given mathematical '
            'statement in {formal_language}.\n'
            'Your task is to refine the given formal code to make it syntactically correct while '
            'maintaining the alignment with the given natural language mathematical statement.\n'
            'Here are some instructions for your task:\n'
            '1. You should give the formal code directly without any additional explanation or any proof.\n'
            '2. In case that you need to import any necessary preambles, you should not import '
            'any fake (non-exist) preambles.\n'
            '3. You should wrap the formal code in a way illustrated as the following:\n'
            '%%%%%%%%%%\n'
            'Your Formal Code\n'
            '%%%%%%%%%%\n'
            '{additional_instructions}'
            'Strictly follow the instructions that have been claimed.\n'
        )

        if category == 'syn':
            additional_instructions = (
                '4. You should make sure that every symbol you use is a valid {formal_language} symbol.\n'
                '5. Some words are reserves as keywords in {formal_language}. You should be careful with '
                'this and avoid to use them to define new names.\n'
                '6. You should make sure that the usage of symbols and operators is correct in your final output as '
                'the incorrect usage will lead to syntax errors.\n'
            )
        elif category == 'udf':
            additional_instructions = (
                '4. You should make sure that every item you mentioned in your code has a clear reference either '
                'in the local context or the dependency files that you decide to import.\n'
            )
        elif category == 'tuf':
            additional_instructions = (
                '4. You should make sure that in your code, the types of operands of operators or the types of '
                'parameters of functions match the types in their definitions exactly. Failure to maintain such '
                'compatibility will lead to type mismatch errors.\n'
            )
        elif category == 'none':
            additional_instructions = ''
        else:
            raise ValueError('The value of \"category\" argument is incorrect. Please choose from: '
                             '[\"none\", \"syn\", \"udf\", \"tuf\"]')

        basic_user_prompt = (
            'Natural language statement: {{informal_statement}}\n'
            'There are some {formal_language} formal codes describing the given mathematical '
            'statement: {{formalization}}\n'
        )

        simple_refinement = (
            'You should refine this piece of formal code for your task.'
        )

        binary_refinement = (
            'You should refine this piece of formal code for your task.'
            'The syntactic correctness for this piece of code is: {{correctness}}.\n'
        )

        detailed_refinement = (
            'You should refine this piece of formal code for your task.'
            'The provided code might have some errors according to the relevant theorem prover. '
            'The error details and where the error part is located in the code are: {{error_details}}\n'
        )

        placeholder = {'informal': '{informal_statement}',
                       'formalization': '{formalization}',
                       'correctness': '{correctness}',
                       'error_details': '{error_details}'}

        self.llm = llm

        self.formal_language = formal_language
        self.system_prompt = basic_system_prompt.replace('{additional_instructions}', additional_instructions)
        self.system_prompt = self.system_prompt.replace(
            '{formal_language}', self.formal_language)
        self.basic_user_prompt = basic_user_prompt.replace(
            '{formal_language}', self.formal_language)
        self.refinement_prompt = {
            'simple': simple_refinement,
            'binary': binary_refinement,
            'detailed': detailed_refinement
        }
        self.placeholder = placeholder

    def get_messages(self,
                     informal_statement: str = '',
                     refinement_mode: str = 'simple',
                     formalization: str = '',
                     correctness: Optional[str] = None,
                     error_details: Optional[str] = None):
        messages = [{'role': 'system', 'content': self.system_prompt}]
        basic_user_content = self.basic_user_prompt.replace(
            self.placeholder['informal'], informal_statement)
        basic_user_content = basic_user_content.replace(
            self.placeholder['formalization'], formalization)

        refinement_content = self.refinement_prompt[refinement_mode]
        if correctness is not None:
            refinement_content = refinement_content.replace(
                self.placeholder['correctness'], correctness)
        if error_details is not None:
            refinement_content = refinement_content.replace(
                self.placeholder['error_details'], error_details)

        user_content = basic_user_content + refinement_content
        messages.append({'role': 'user', 'content': user_content})
        return messages

    def _agent_function(self,
                        informal_statement: str = '',
                        refinement_mode: str = 'simple',
                        formalization: str = '',
                        correctness: Optional[str] = None,
                        error_details: Optional[str] = None):
        messages = self.get_messages(informal_statement=informal_statement,
                                     refinement_mode=refinement_mode,
                                     formalization=formalization,
                                     correctness=correctness,
                                     error_details=error_details)
        response = self.llm.generate(messages)
        return extract_formal_code(response), response
