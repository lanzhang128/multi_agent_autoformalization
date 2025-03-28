import json
from tqdm import tqdm
from llm import OpenAILLM, HuggingFaceLLM
from agent import AutoformalizationAgent, DenoisingAgent


if __name__ == '__main__':
    # Prepare three examples for few-shot autoformalization
    informal_formal_pairs = [
        [
            "Determine the value of $ab$ if $\\log_8a+\\log_4b^2=5$ and $\\log_8b+\\log_4a^2=7$. Show that it is 512.",
            "theory aime_1984_p5 imports Complex_Main\nbegin\n\ntheorem aime_1984_p5:\n  fixes a b ::real\n  assumes "
            "\"(ln a) / (ln 8) + (ln (b^2)) / (ln 4) = 5\"\n          \"(ln b) / (ln 8) + (ln (a^2)) / (ln 4) = 7\"\n "
            "       shows \"a * b = 512\"\n  sorry\n\nend\n"
        ],
        [
            "One dimension of a cube is increased by $1$, another is decreased by $1$, and the third is left "
            "unchanged. The volume of the new rectangular solid is $5$ less than that of the cube. What was the "
            "volume of the cube?\n\n$\\textbf{(A)}\\ 8 \\qquad \\textbf{(B)}\\ 27 \\qquad \\textbf{(C)}\\ 64 \\qquad "
            "\\textbf{(D)}\\ 125 \\qquad \\textbf{(E)}\\ 216$ Show that it is \\text{(D)}.",
            "theory amc12a_2009_p5 imports\n  Complex_Main\nbegin\n\ntheorem amc12a_2009_p5:\n  fixes x :: real\n  "
            "assumes h0 : \"x^3 - (x+1) * (x-1) * x = 5\"\n  shows \"x^3 = 125\"\n  sorry\n\nend"
        ],
        [
            "Solve the system of equations\n\n$|a_1 - a_2| x_2 +|a_1 - a_3| x_3 +|a_1 - a_4| x_4 = 1\\\\ |a_2 - a_1| "
            "x_1 +|a_2 - a_3| x_3 +|a_2 - a_4| x_4 = 1\\\\ |a_3 - a_1| x_1 +|a_3 - a_2| x_2 +|a_3-a_4|x_4= 1\\\\ |a_4 "
            "- a_1| x_1 +|a_4 - a_2| x_2 +|a_4 - a_3| x_3 = 1$\n\nwhere $a_1, a_2, a_3, a_4$ are four different real "
            "numbers.",
            "theory imo_1966_p5 imports\nComplex_Main\n\nbegin\n\ntheorem imo_1966_p5:\n  fixes x a :: \"nat "
            "\\<Rightarrow> real\"\n  assumes \"a 1 > a 2\" and \"a 2 > a 3\" and \"a 3 > a 4\"\n  assumes \n    h6 : "
            "\"abs (a 1 - a 2) * x 2 + abs (a 1 - a 3) * x 3 + abs (a 1 - a 4) * x 4 = 1\"\n    and h7 : \"abs (a 2 - "
            "a 1) * x 1 + abs (a 2 - a 3) * x 3 + abs (a 2 - a 4) * x 4 = 1\"\n    and h8 : \"abs (a 3 - a 1) * x 1 + "
            "abs (a 3 - a 2) * x 2 + abs (a 3 - a 4) * x 4 = 1\"\n    and h9 : \"abs (a 4 - a 1) * x 1 + abs (a 4 - a "
            "2) * x 2 + abs (a 4 - a 3) * x 3 = 1\"\n  shows \"x 2 = 0 \\<and> x 3 = 0 \\<and> x 1 = 1 / abs (a 1 - a "
            "4) \\<and> x 4 = 1 / abs (a 1 - a 4)\"\n  sorry\n\nend"
        ]
    ]

    # Instantiate LLMs
    with open('../api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read()
    gpt_4o = OpenAILLM(
        name='gpt-4o',
        api_key=api_key,
        model='gpt-4o'
    )

    mistral = HuggingFaceLLM(
        name='mistral',
        model_id='mistralai/Mistral-7B-Instruct-v0.2')

    # Set formal language
    formal_language = 'Isabelle/HOL'

    # Instantiate Agents
    agent_auto = AutoformalizationAgent(
        llm=mistral,
        name='autoformalization',
        formal_language=formal_language
    )

    agent_denoising = DenoisingAgent(
        llm=gpt_4o,
        name='denoising',
        formal_language=formal_language
    )

    with open('minif2f_subset_test.json', 'r', encoding='utf-8') as f:
        json_dic = json.load(f)

    res = {'3-shot': {},
           'denoising': {}}

    for key in tqdm(json_dic.keys()):
        informal = json_dic[key]['latex']
        formalization, _ = agent_auto(
            informal_statement=informal, informal_formal_pairs=informal_formal_pairs)
        cleaned_formalization, _ = agent_denoising(formalization=formalization)
        res['3-shot'][key] = {'formalization': formalization}
        res['denoising'][key] = {'formalization': cleaned_formalization}

        with open('denoising.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
