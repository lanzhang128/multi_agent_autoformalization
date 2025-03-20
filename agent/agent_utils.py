import re


def extract_formal_code(text):
    code = re.findall('%%%%%%%%%%.*?%%%%%%%%%%', text, flags=re.DOTALL)
    if code:
        code = code[0]
    else:
        code = text
    return code.replace('%%%%%%%%%%\n', '').replace('%%%%%%%%%%', '')


def extract_judgement(text):
    code = re.findall('%%%%%%%%%%.*?%%%%%%%%%%', text, flags=re.DOTALL)
    if code:
        code = code[0]
    else:
        code = text
    return code.replace('%%%%%%%%%%\n', '').replace('%%%%%%%%%%', '')
