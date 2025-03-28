import json
from tqdm import tqdm
from llm import OpenAILLM
from agent import HardCritiqueAgent, FormalRefinementAgent


if __name__ == '__main__':
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

    with open('minif2f_subset_test.json', 'r', encoding='utf-8') as f:
        json_dic = json.load(f)

    with open('self_improving.json', 'r', encoding='utf-8') as f:
        can_json = json.load(f)

    n = 10
    res = {str(i): {} for i in range(n+1)}
    for temp in ['zero', '3']:
        formalizations = can_json[f'{temp}-shot']
        for key in tqdm(json_dic.keys()):
            informal = json_dic[key]['latex']
            formalization = formalizations[key]['formalization']
            for i in range(n):
                correctness, error_details = agent_hard(
                    formalization=formalization,
                    file_prefix='test')
                res[str(i)][key] = {'formalization': formalization,
                                    'correctness': correctness,
                                    'error_details': error_details}

                if correctness != 'True':
                    formalization, _ = agent_formal(
                        informal_statement=informal,
                        refinement_mode='detailed',
                        formalization_file='../test_results/test.thy',
                        correctness=correctness,
                        error_details=error_details)

            res[str(n)][key] = {'formalization': formalization}

            with open('iterative.json', 'w', encoding='utf-8') as f:
                json.dump(res, f, ensure_ascii=False, indent=4)

    agent_hard.theorem_prover.terminate()
