import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .abstract import BaseLLM


class HuggingFaceLLM(BaseLLM):
    description = 'Class for instantiating a HuggingFace LLM.'

    def __init__(self,
                 name: str = 'HuggingFaceLLM',
                 model_id: str = 'meta-llama/Meta-Llama-3-8B-Instruct',
                 max_new_tokens: int = 1000,
                 do_sample: bool = False):
        super().__init__(name, model_id=model_id)
        self.max_new_tokens = max_new_tokens
        self.do_sample = do_sample

    def _instantiate(self, model_id):
        self.model_id = model_id
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id, device_map='auto', torch_dtype=torch.float16)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)

    def generate(self, messages):
        encodeds = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors='pt')
        model_inputs = encodeds.to('cuda')
        generated_ids = self.model.generate(
            model_inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=self.do_sample,
            pad_token_id=self.tokenizer.eos_token_id)
        decoded = self.tokenizer.batch_decode(generated_ids)[0]
        template = self.tokenizer.batch_decode(encodeds)[0]
        return decoded[decoded.find(template) + len(template):]
