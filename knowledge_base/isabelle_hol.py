import os
import json
from .abstract import BaseKnowledgeBase


class IsabelleHOLKnowledgeBase(BaseKnowledgeBase):
    description = 'Class for a knowledge base constructed from Isabelle/HOL.'
    metadata_file = os.path.join(os.path.dirname(__file__), 'metadata/Isabelle_HOL.json')

    def __init__(self,
                 name: str = 'IsabelleHOLKnowledgeBase'):
        super().__init__(name)
        self.formal_statements = self.select_key('statement')

    def _fill_data(self):
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.metadata += data.values()
