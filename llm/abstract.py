from abc import ABC, abstractmethod


class BaseLLM(ABC):
    description = 'Abstract class for instantiating LLMs.'

    def __init__(self,
                 name: str = 'BaseLLM',
                 **kwargs):
        self.name = name
        self._instantiate(**kwargs)

    @abstractmethod
    def _instantiate(self, **kwargs):
        pass

    @abstractmethod
    def generate(self, messages):
        pass
