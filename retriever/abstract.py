from abc import ABC, abstractmethod


class BaseRetriever(ABC):
    description = 'Abstract class for retrievers.'

    def __init__(self,
                 name: str = 'BaseRetriever',
                 **kwargs):
        self.name = name
        self._instantiate(**kwargs)

    @abstractmethod
    def _instantiate(self, **kwargs):
        pass

    @abstractmethod
    def retrieve(self, query, **kwargs):
        pass
