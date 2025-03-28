import json
from tqdm import tqdm
from llm import OpenAILLM
from agent import (AutoformalizationAgent,
                   HardCritiqueAgent, FormalRefinementAgent,
                   SoftCritiqueAgent, InformalRefinementAgent)


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
    gpt_4o_mini = OpenAILLM(
        name='gpt-4o-mini',
        api_key=api_key,
        model='gpt-4o-mini'
    )

    # Set formal language
    formal_language = 'Isabelle/HOL'

    # Instantiate Agents
    agent_auto = AutoformalizationAgent(
        llm=gpt_4o_mini,
        name='autoformalization',
        formal_language=formal_language
    )

    agent_hard = HardCritiqueAgent(
        name='theorem prover',
        formal_language=formal_language,
        file_dir='../test_results',
    )
    agent_hard.theorem_prover.verbose = False

    agent_formal = FormalRefinementAgent(
        llm=gpt_4o_mini,
        name='formal refinement',
        formal_language=formal_language
    )

    aspect_description = ('whether the formalized code involves all mathematical concepts in the natural language '
                          'statement.')

    agent_soft = SoftCritiqueAgent(
        llm=gpt_4o_mini,
        name='soft critique',
        formal_language=formal_language,
        aspect_description=aspect_description)

    agent_informal = InformalRefinementAgent(
        llm=gpt_4o_mini,
        name='informal refinement',
        formal_language=formal_language)

    with open('minif2f_subset_test.json', 'r', encoding='utf-8') as f:
        json_dic = json.load(f)

    res = {'zero-shot': {},
           '3-shot': {},
           'zero-shot+hcfr': {},
           '3-shot+hcfr': {},
           'zero-shot+scir': {},
           '3-shot+scir': {}}

    for key in tqdm(json_dic.keys()):
        informal = json_dic[key]['latex']
        for temp in ['zero', '3']:
            if temp == 'zero':
                formalization, _ = agent_auto(
                    informal_statement=informal)
            else:
                formalization, _ = agent_auto(
                    informal_statement=informal, informal_formal_pairs=informal_formal_pairs)
            correctness, error_details = agent_hard(
                formalization=formalization,
                file_prefix='test')

            if correctness != 'True':
                detailed_refinement, _ = agent_formal(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization_file='../test_results/test.thy',
                    correctness=correctness,
                    error_details=error_details)
            else:
                detailed_refinement = formalization

            aspect_evaluation, _ = agent_soft(
                informal_statement=informal,
                formalization=formalization)

            informal_refinement, _ = agent_informal(
                informal_statement=informal,
                formalization=formalization,
                aspect_description=aspect_description,
                aspect_evaluation=aspect_evaluation)

            res[f'{temp}-shot'][key] = {'formalization': formalization,
                                        'error_details': error_details,
                                        'aspect_evaluation': aspect_evaluation}
            res[f'{temp}-shot+hcfr'][key] = {'formalization': detailed_refinement}
            res[f'{temp}-shot+scir'][key] = {'formalization': informal_refinement}

        with open('self_improving.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)

    agent_hard.theorem_prover.terminate()
