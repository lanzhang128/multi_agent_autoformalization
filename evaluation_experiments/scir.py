import re
import json
from tqdm import tqdm
from llm import OpenAILLM, HuggingFaceLLM
from agent import AutoformalizationAgent, SoftCritiqueAgent, InformalRefinementAgent
from dataset import MiniF2F


def judge_value(text):
    judgement = re.findall('Judgement: (True|False)', text, flags=re.DOTALL)
    if judgement:
        correctness = judgement[-1].split()[-1]
        if correctness == 'True':
            return True
        else:
            return False
    else:
        return None


if __name__ == '__main__':
    pairs = [
        [
            "Given that\n\n$$\n\\begin{align*}x_{1}&=211,\\\\\nx_{2}&=375,\\\\\nx_{3}&=420,\\\\\nx_{4}&=523,"
            "\\ \\text{and}\\\\\nx_{n}&=x_{n-1}-x_{n-2}+x_{n-3}-x_{n-4}\\ \\text{when}\\ n\\geq5, "
            "\\end{align*}\n$$\n\nfind the value of $x_{531}+x_{753}+x_{975}$. Show that it is 898.",
            "import Mathlib\n\nopen BigOperators Real Nat Topology\n\ntheorem aimeII_2001_p3\n  (x : ℕ → ℤ)\n  (h₀ : "
            "x 1 = 211)\n  (h₂ : x 2 = 375)\n  (h₃ : x 3 = 420)\n  (h₄ : x 4 = 523)\n  (h₆ : ∀ n ≥ 5, x n = x (n - 1) "
            "- x (n - 2) + x (n - 3) - x (n - 4)) :\n  x 531 + x 753 + x 975 = 898 := sorry"
        ],
        [
            "Show that for any complex number $x$, $x^2 + 49 = (x + 7i)(x - 7i)$.",
            "import Mathlib\n\nopen BigOperators Real Nat Topology\n\ntheorem "
            "algebra_2complexrootspoly_xsqp49eqxp7itxpn7i\n  (x : ℂ) :\n  x^2 + 49 = (x + (7 * Complex.I)) * (x + (-7 "
            "* Complex.I)) := sorry"
        ],
        [
            "Compute the sum of all the roots of\n$(2x+3)(x-4)+(2x+3)(x-6)=0 $\n\n$ \\textbf{(A) } \\frac{7}{"
            "2}\\qquad \\textbf{(B) } 4\\qquad \\textbf{(C) } 5\\qquad \\textbf{(D) } 7\\qquad \\textbf{(E) } 13 $ "
            "Show that it is \\textbf{(A) }7/2.",
            "import Mathlib\n\nopen BigOperators Real Nat Topology\n\ntheorem amc12a_2002_p1\n  (f : ℂ → ℂ)\n  (h₀ : "
            "∀ x, f x = (2 * x + 3) * (x - 4) + (2 * x + 3) * (x - 6))\n  (h₁ : Fintype (f ⁻¹' {0})) :\n  ∑ y in ("
            "f⁻¹' {0}).toFinset, y = 7 / 2 := sorry"
        ]
    ]

    # Instantiate LLMs
    with open('../api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read().rstrip()
    gpt_mini = OpenAILLM(
        name='gpt-mini',
        api_key=api_key,
        model='gpt-4.1-mini'
    )

    fl = 'Lean4'

    aspect = {
        'af': 'Is the formalized code accurately aligned with the intended semantics of natural language statement?',
        'fc': 'Is the formalized code alone valid, nature and well-formed?'
    }
    sca = {
        'af': SoftCritiqueAgent(llm=gpt_mini, formal_language=fl, aspect_description=aspect['af']),
        'fc': SoftCritiqueAgent(llm=gpt_mini, formal_language=fl, aspect_description=aspect['fc'])
    }

    test_set = MiniF2F(split='test')

    for name, model_id in [('qwen', 'Qwen/Qwen2.5-7B-Instruct'), ('ds', 'deepseek-ai/deepseek-math-7b-instruct')]:
        model = HuggingFaceLLM(model_id=model_id)
        res = {name: {},
               f'{name}_sc': {}}
        for a in ['af', 'fc']:
            res[f'{name}_ir_{a}'] = {}
            res[f'{name}_ir_{a}_sc'] = {}
            res[f'{name}_ir_gpt_{a}'] = {}
            res[f'{name}_ir_gpt_{a}_sc'] = {}

        afa = AutoformalizationAgent(
            llm=model,
            name='autoformalization agent',
            formal_language=fl)
        ira = InformalRefinementAgent(
            name='informal refinement',
            llm=model,
            formal_language=fl)
        ira_gpt = InformalRefinementAgent(
            name='informal refinement with gpt-4.1-mini',
            llm=gpt_mini,
            formal_language=fl)

        for key, sample in tqdm(zip(test_set.keys, test_set.data), total=len(test_set.keys)):
            informal = sample.informal
            formal, _ = afa(
                informal_statement=informal, informal_formal_pairs=pairs)
            res[name][key] = formal

            res[f'{name}_sc'][key] = {}
            for a in ['af', 'fc']:
                res[f'{name}_sc'][key][a] = sca[a](informal_statement=informal, formalization=formal)[0]

                if not judge_value(res[f'{name}_sc'][key][a]):
                    refinement, _ = ira(
                        informal_statement=informal,
                        formalization=formal,
                        aspect_description=aspect[a],
                        aspect_evaluation=res[f'{name}_sc'][key][a])
                    res[f'{name}_ir_{a}'][key] = refinement
                    res[f'{name}_ir_{a}_sc'][key] = {}
                    for b in ['af', 'fc']:
                        res[f'{name}_ir_{a}_sc'][key][b] = sca[b](informal_statement=informal, formalization=refinement)[0]

                    refinement, _ = ira_gpt(
                        informal_statement=informal,
                        formalization=formal,
                        aspect_description=aspect[a],
                        aspect_evaluation=res[f'{name}_sc'][key][a])
                    res[f'{name}_ir_gpt_{a}'][key] = refinement
                    res[f'{name}_ir_gpt_{a}_sc'][key] = {}
                    for b in ['af', 'fc']:
                        res[f'{name}_ir_gpt_{a}_sc'][key][b] = sca[b](informal_statement=informal, formalization=refinement)[0]
                else:
                    res[f'{name}_ir_{a}'][key] = formal
                    res[f'{name}_ir_{a}_sc'][key] = res[f'{name}_sc'][key]
                    res[f'{name}_ir_gpt_{a}'][key] = formal
                    res[f'{name}_ir_gpt_{a}_sc'][key] = res[f'{name}_sc'][key]

            for a in res.keys():
                with open(f'../test_results/minif2f/{a}.json', 'w', encoding='utf-8') as f:
                    json.dump(res[a], f, ensure_ascii=False, indent=4)
