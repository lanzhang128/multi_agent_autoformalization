import re
import json
from tqdm import tqdm
from llm import OpenAILLM, HuggingFaceLLM
from agent import (AutoformalizationAgent,
                   HardCritiqueAgent, FormalRefinementAgent,
                   SoftCritiqueAgent, InformalRefinementAgent)
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
    fl = 'Lean4'
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

    qwen = HuggingFaceLLM(name='qwen2.5-7B', model_id='Qwen/Qwen2.5-7B-Instruct')

    afa = AutoformalizationAgent(
        llm=qwen,
        name='autoformalization agent',
        formal_language=fl)

    hca = HardCritiqueAgent(
        name='theorem prover',
        formal_language=fl,
        file_dir=f'../test_results/minif2f')

    with open('../api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read().rstrip()
    gpt_mini = OpenAILLM(
        name='gpt-mini',
        api_key=api_key,
        model='gpt-4.1-mini')

    aspect = 'Is the formalized code accurately aligned with the intended semantics of natural language statement?'
    sca = SoftCritiqueAgent(llm=gpt_mini, formal_language=fl, aspect_description=aspect)

    fra = FormalRefinementAgent(
        name='formal refinement with qwen2.5-7B',
        llm=qwen,
        formal_language=fl)

    ira = InformalRefinementAgent(
        name='informal refinement with qwen2.5-7B',
        llm=qwen,
        formal_language=fl)

    test_set = MiniF2F(split='test')

    res = {f'qwen_{i}': {} for i in range(5)}

    for key, sample in tqdm(zip(test_set.keys, test_set.data), total=len(test_set.keys)):
        informal = sample.informal
        formal, _ = afa(
            informal_statement=informal, informal_formal_pairs=pairs)

        correctness, error_details = hca(formalization=formal, file_prefix=f'qwen_0_{key}')
        judgment = sca(informal_statement=informal, formalization=formal)[0]
        res['qwen_0'][key] = {'code': formal,
                              'hard': correctness + '\n' + error_details,
                              'soft': judgment}

        for j in range(4):
            if correctness != 'True':
                with open(f'../test_results/minif2f/qwen_{j}_{key}.lean', 'r', encoding='utf-8') as f:
                    formalization = f.read()
                formal, _ = fra(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization=formalization,
                    correctness=correctness,
                    error_details=error_details)
                correctness, error_details = hca(formalization=formal, file_prefix=f'qwen_{j + 1}_{key}')
                judgment = sca(informal_statement=informal, formalization=formal)[0]
                res[f'qwen_{j + 1}'][key] = {'code': formal,
                                             'hard': correctness + '\n' + error_details,
                                             'soft': judgment}
            else:
                if not judge_value(judgment):
                    formal, _ = ira(
                        informal_statement=informal,
                        formalization=formal,
                        aspect_description=aspect,
                        aspect_evaluation=judgment)
                    correctness, error_details = hca(formalization=formal, file_prefix=f'qwen_{j + 1}_{key}')
                    judgment = sca(informal_statement=informal, formalization=formal)[0]
                    res[f'qwen_{j + 1}'][key] = {'code': formal,
                                                 'hard': correctness + '\n' + error_details,
                                                 'soft': judgment}
                else:
                    res[f'qwen_{j + 1}'][key] = {'code': formal,
                                                 'hard': correctness + '\n' + error_details,
                                                 'soft': judgment}

        for a in res.keys():
            with open(f'../test_results/minif2f/{a}.json', 'w', encoding='utf-8') as f:
                json.dump(res[a], f, ensure_ascii=False, indent=4)
