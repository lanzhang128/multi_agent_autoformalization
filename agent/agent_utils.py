import re
import json
from llm import OpenAILLM, HuggingFaceLLM


def no_postprocess(text):
    return text


def postprocess(text):
    code = re.findall('%%%%%%%%%%.*?%%%%%%%%%%', text, flags=re.DOTALL)
    if code:
        code = code[0]
    else:
        code = text
    return code.replace('%%%%%%%%%%\n', '').replace('%%%%%%%%%%', '')


def get_postprocess_fn(llm):
    return postprocess
