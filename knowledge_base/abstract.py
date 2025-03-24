from abc import ABC, abstractmethod


class BaseKnowledgeBase(ABC):
    description = 'Abstract class for knowledge bases.'

    def __init__(self,
                 name: str = 'BaseKnowledgeBase'):
        self.name = name
        self.metadata = []
        self._fill_data()

    def __getitem__(self, item):
        return self.metadata[item]

    @abstractmethod
    def _fill_data(self):
        pass

    def select_key(self, key):
        return [temp[key] for temp in self.metadata]
