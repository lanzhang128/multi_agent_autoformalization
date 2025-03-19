from llm import OpenAILLM, HuggingFaceLLM
from agent import AutoformalizationAgent, FormalRefinementAgent, HardCritiqueAgent, DenoisingAgent


if __name__ == '__main__':
    # Instantiate LLMs
    with open('api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read()
    gpt_4o_mini = OpenAILLM(
        name='gpt-4o-mini',
        api_key=api_key,
        model='gpt-4o-mini'
    )

    '''deepseekmath = HuggingFaceLLM(
        name='deepseekmath',
        model_id='deepseek-ai/deepseek-math-7b-instruct'
    )'''
    
    print('LLMs are instantiated.')
    
    # Set formal language
    formal_language = 'Isabelle/HOL'
    
    # Instantiate Agents
    agent_autoformalization = AutoformalizationAgent(
        llm=gpt_4o_mini,
        name='autoformalization',
        formal_language=formal_language
    )

    agent_hardenoising = DenoisingAgent(
        llm=gpt_4o_mini,
        name='denoising',
        formal_language=formal_language
    )

    agent_refinement = FormalRefinementAgent(
        llm=gpt_4o_mini,
        name='formal refinement',
        formal_language=formal_language
    )

    agent_hard = HardCritiqueAgent(
        name='theorem prover',
        formal_language=formal_language,
        file_dir='test_results'
    )
    print('Agents are instantiated.')
    input("Press Enter to continue...")

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

    print('Here are examples used:')
    for informal, formal in zip(informal_formal_pairs):
        print(f'informal: {informal}')
        print(f'formal: {formal}')

    input("Press Enter to continue...")

    # Prepare a natural language mathematical statement
    informal = ("Definition of Equalized Odds: Equalized odds is a measure of fairness in machine learning. "
                "A classifier satisfies this definition if the subjects in the protected and unprotected groups have "
                "equal true positive rate and equal false positive rate, satisfying the formula: "
                "\\[P(R = + | Y = y, A = a) = P(R = + | Y = y, A = b) \\quad y \\in \\{+,-\\} \\quad "
                "\\forall a,b \\in A\\]")
    print('Test natural language example:')
    print(informal)

    input("Press Enter to continue...")
    print('=' * 20)
    print('GPT-4o-mini zero-shot:')
    zero_formalization, response = agent_autoformalization(informal_statement=informal)
    print('formalization:')
    print(zero_formalization)
    print('response:')
    print(response)

    input("Press Enter to continue...")
    print('=' * 20)
    print('GPT-4o-mini 3-shot:')
    shot_formalization, _ = agent_autoformalization(informal_statement=informal, informal_formal_pairs=informal_formal_pairs)
    print('formalization:')
    print(shot_formalization)

    input("Press Enter to continue...")
    print('=' * 20)
    print('GPT-4o-mini cleaned 3-shot:')
    cleaned_formalization, _ = agent_hardenoising(formalization=shot_formalization)
    print('formalization:')
    print(cleaned_formalization)

    input("Press Enter to continue...")
    print('=' * 20)
    print('testing previous zero-shot autoformalization')
    correctness, error_details = agent_hard(
        formalization=zero_formalization,
        file_prefix='test'
    )
    print(correctness)
    print(error_details)

    input("Press Enter to continue...")
    print('=' * 20)
    print('simple refinement:')
    simple_refinement, response = agent_refinement(
        informal_statement=informal,
        refinement_mode='simple',
        formalization=zero_formalization
    )
    print('formalization:')
    print(simple_refinement)

    input("Press Enter to continue...")
    print('=' * 20)
    print('binary refinement:')
    binary_refinement, response = agent_refinement(
        informal_statement=informal,
        refinement_mode='binary',
        formalization=zero_formalization,
        correctness=correctness
    )
    print('formalization:')
    print(binary_refinement)

    input("Press Enter to continue...")
    print('=' * 20)
    print('detailed refinement:')
    detailed_refinement, response = agent_refinement(
        informal_statement=informal,
        refinement_mode='detailed',
        formalization=zero_formalization,
        error_details=error_details
    )
    print('formalization:')
    print(detailed_refinement)

    input("Press Enter to continue...")
    agent_hard.theorem_prover.terminate()
