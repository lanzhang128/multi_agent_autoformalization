import re
from retriever import BM25Retriever
from knowledge_base import IsabelleHOLKnowledgeBase
from .abstract import BaseAgent


class ImportRetrievalAgent(BaseAgent):
    description = 'An Agent for retrieving imports for formalization codes.'

    def __init__(self,
                 name: str = 'ImportRetrievalAgent',
                 formal_language: str = 'Isabelle/HOL',
                 retriever: str = 'bm25'):
        super().__init__(name=name)

        self.formal_language = formal_language
        if self.formal_language == 'Isabelle/HOL':
            self.knowledge_base = IsabelleHOLKnowledgeBase()
        else:
            raise ValueError(f'{formal_language} is not supported.')

        if retriever == 'bm25':
            self.retriever = BM25Retriever(
                corpus=self.knowledge_base.formal_statements, formal_language=self.formal_language)
        else:
            raise ValueError(f'{retriever} is not supported, please select from [\"bm25\"].')

    def _agent_function(self,
                        formalization: str = '',
                        top_n=3):
        imports = re.findall('imports.*begin', formalization, flags=re.DOTALL)
        if imports:
            imports = imports[0][7:-5].split()
        else:
            imports = ['Main']

        ids = self.retriever.retrieve(query=formalization, top_n=top_n)
        imports += ['\"' + self.knowledge_base[i]['source'] + '\"' for i in ids]
        imports = '\n'.join(list(set(imports)))

        code = re.findall('begin.*end', formalization, flags=re.DOTALL)
        if code:
            code = code[0]
        else:
            code = 'begin\n' + formalization + '\nend'

        return f'imports\n{imports}\n{code}'
