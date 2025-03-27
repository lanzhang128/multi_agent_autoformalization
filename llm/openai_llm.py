from .abstract import BaseLLM
from openai import OpenAI
import tenacity


class OpenAILLM(BaseLLM):
    description = 'Class for instantiating an OpenAI LLM.'

    def __init__(self,
                 name: str = 'OpenAILLM',
                 api_key: str = '',
                 model: str = 'gpt-4o-mini',
                 max_tokens: int = 1000,
                 temperature: float = 0.2):
        super().__init__(name, api_key=api_key, model=model)
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _instantiate(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=30))
    def completion_with_backoff(self, **kwargs):
        try:
            return self.client.chat.completions.create(
                model=self.model, **kwargs)
        except Exception as e:
            print(e)
            raise e

    def generate(self, messages):
        try:
            response = self.completion_with_backoff(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens)
        except Exception as e:
            print('Error:', e)
            return

        return response.choices[0].message.content
