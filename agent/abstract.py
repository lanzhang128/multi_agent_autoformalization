from abc import ABC, abstractmethod


class BaseAgent(ABC):
    description = 'Abstract class for constructing agents.'

    def __init__(self,
                 name: str = 'BaseAgent'):
        self.name = name

    @abstractmethod
    def _agent_function(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self._agent_function(*args, **kwargs)
