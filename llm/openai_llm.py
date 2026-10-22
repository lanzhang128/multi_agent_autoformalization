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
        try:
            self.client.responses.create(
                model=self.model,
                input="Say hello.",
                temperature=0.2,
                max_output_tokens=100)
            self.support_temperature = True
        except Exception as e:
            print(f"{model}: {e}")
            self.support_temperature = False

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=30))
    def completion_with_backoff(self, **kwargs):
        try:
            return self.client.responses.create(
                model=self.model, **kwargs)
        except Exception as e:
            print(e)
            raise e

    def generate(self, messages):
        try:
            if self.support_temperature:
                response = self.completion_with_backoff(
                    input=messages,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens)
            else:
                response = self.completion_with_backoff(
                    input=messages,
                    max_output_tokens=self.max_tokens)
        except Exception as e:
            print('Error:', e)
            return

        return response.output_text
