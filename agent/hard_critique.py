import os
import tempfile
import re
from theorem_prover import Isabelle, isabelle_get_error_details
from .abstract import BaseAgent


class HardCritiqueAgent(BaseAgent):
    description = 'Hard critique of autoformalzation from the relevant theorem prover.'

    def __init__(self,
                 name: str = 'HardCritiqueAgent',
                 formal_language: str = 'Isabelle/HOL',
                 file_dir: str = tempfile.mkdtemp()):
        super().__init__(name=name)

        self.formal_language = formal_language
        if self.formal_language[:8] == 'Isabelle':
            self.theorem_prover = Isabelle(
                default_session=formal_language.split('/')[-1],
                log_file=os.path.join(file_dir, 'isabelle.log')
            )
        else:
            raise ValueError(f'{formal_language} is not supported.')

        self.file_dir = file_dir

    def isabelle_process(self,
                         formalization: str = '',
                         file_prefix: str = 'test'):
        code = re.findall('imports.*end', formalization, flags=re.DOTALL)
        if code:
            code = code[0]
        else:
            code = 'imports Main\nbegin\n' + formalization + '\nend'

        file_path = os.path.join(self.file_dir, file_prefix + '.thy')
        error_log_path = os.path.join(self.file_dir, file_prefix + '.error.log')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'theory {file_prefix}\n{code}')
        finished_response, inference_time = self.theorem_prover.use_theories(
            theories=[file_prefix], master_dir=self.file_dir)
        is_valid, error_lines, error_details = isabelle_get_error_details(finished_response=finished_response)
        with open(error_log_path, 'w', encoding='utf-8') as file:
            file.write(f'logical validity: {is_valid}\n')
            file.write(f'error lines: {error_lines}\n')
            file.write(f'errors details: {error_details}\n')
            file.write(f'isabelle inference time: {inference_time:.2f}s')

        all_syntax_error = ''
        for i, line_number in enumerate(error_lines):
            detail = error_details[i]
            line, start, end = int(detail.split()[3][:-1]), int(detail.split()[5][:-1]), int(detail.split()[7][:-1])
            assert line == error_lines[i]
            message = detail[detail.find(':') + 2:]
            syntax_error = (f'Identified error on line: {line}\n'
                            f'Error message: {message}\n')

            all_syntax_error += f'{syntax_error}\n'
        return str(is_valid), all_syntax_error

    def _agent_function(self,
                        formalization: str = '',
                        file_prefix: str = 'test'):
        if self.formal_language[:8] == 'Isabelle':
            correctness, error_details = self.isabelle_process(formalization, file_prefix)
            return correctness, error_details
        else:
            return None, None
