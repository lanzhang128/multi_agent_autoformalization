import json
import shutil
from tqdm import tqdm
from llm import OpenAILLM, HuggingFaceLLM
from agent import AutoformalizationAgent, HardCritiqueAgent, FormalRefinementAgent
from dataset import MiniF2F, ProofNet

if __name__ == '__main__':
    pairs = {
        'minif2f': [
            [
                "Given that\n\n$$\n\\begin{align*}x_{1}&=211,\\\\\nx_{2}&=375,\\\\\nx_{3}&=420,\\\\\nx_{4}&=523,"
                "\\ \\text{and}\\\\\nx_{n}&=x_{n-1}-x_{n-2}+x_{n-3}-x_{n-4}\\ \\text{when}\\ n\\geq5, "
                "\\end{align*}\n$$\n\nfind the value of $x_{531}+x_{753}+x_{975}$. Show that it is 898.",
                "theory aimeII_2001_p3 imports\n  Complex_Main\nbegin\n\ntheorem aimeII_2001_p3:\n  fixes x :: \"nat "
                "\\<Rightarrow> int\"\n  assumes h0 : \"x 1 = 211\"\n    and h1 : \"x 2 = 375\"\n    and h2 : \"x 3 = "
                "420\"\n    and h3 : \"x 4 = 523\"\n    and h4 : \"\\<And>(n::nat). ((n\\<ge>5) \\<Longrightarrow> (x "
                "n = x (n-1) - x (n-2) + x (n-3) - x (n-4)))\"\n  shows \"x 531 + x 753 + x 975 = 898\"\n  sorry\n\nend"
            ],
            [
                "Show that for any complex number $x$, $x^2 + 49 = (x + 7i)(x - 7i)$.",
                "theory algebra_2complexrootspoly_xsqp49eqxp7itxpn7i imports\n  Complex_Main\nbegin\n\ntheorem "
                "algebra_2complexrootspoly_xsqp49eqxp7itxpn7i:\n  fixes x :: complex\n  shows \"x^2 + 49 = (x + 7 * "
                "\\<i>) * (x - 7 * \\<i>)\"\n  sorry\n\nend"
            ],
            [
                "Compute the sum of all the roots of\n$(2x+3)(x-4)+(2x+3)(x-6)=0 $\n\n$ \\textbf{(A) } \\frac{7}{"
                "2}\\qquad \\textbf{(B) } 4\\qquad \\textbf{(C) } 5\\qquad \\textbf{(D) } 7\\qquad \\textbf{(E) } 13 "
                "$ Show that it is \\textbf{(A) }7/2.",
                "theory amc12a_2002_p1 imports\n  Complex_Main\n  "
                "\"HOL-Computational_Algebra.Computational_Algebra\"\n  \nbegin\n\ntheorem amc12a_2002_p1:\n  fixes "
                "f::\"complex \\<Rightarrow> complex\"\n  assumes \"\\<forall> x. f x = (2 * x + 3) * (x - 4) + (2 * "
                "x + 3) * (x - 6)\"\n  shows \"(\\<Sum> y \\<in> f -` {0}. y) = 7/2\"\n  sorry\n\nend"
            ]
        ],
        'proofnet': [
            [
                "Let $A$ be a nonempty set of real numbers which is bounded below. Let $-A$ be the set of all numbers "
                "$-x$, where $x \\in A$. Prove that $\\inf A=-\\sup (-A)$.",
                "import Mathlib\n\nopen Topology Filter Real Complex TopologicalSpace Finset\nopen scoped "
                "BigOperators\n\ntheorem exercise_1_5 (A minus_A : Set ℝ) (hA : A.Nonempty)\n  (hA_bdd_below : "
                "BddBelow A) (hminus_A : minus_A = {x | -x ∈ A}) :\n  Inf A = Sup minus_A :=sorry"
            ],
            [
                "Suppose (a) $f$ is continuous for $x \\geq 0$, (b) $f^{\\prime}(x)$ exists for $x>0$, (c) $f(0)=0$, "
                "(d) $f^{\\prime}$ is monotonically increasing. Put $g(x)=\\frac{f(x)}{x} \\quad(x>0)$ and prove that "
                "$g$ is monotonically increasing.",
                "import Mathlib\n\nopen Topology Filter Real Complex TopologicalSpace Finset\nopen scoped "
                "BigOperators\n\ntheorem exercise_5_6\n  {f : ℝ → ℝ}\n  (hf1 : Continuous f)\n  (hf2 : ∀ x, "
                "DifferentiableAt ℝ f x)\n  (hf3 : f 0 = 0)\n  (hf4 : Monotone (deriv f)) :\n  MonotoneOn (λ x => f x "
                "/ x) (Set.Ioi 0) :=sorry"
            ],
            [
                "Prove that $\\sum 1/k(\\log(k))^p$ diverges when $p \\leq 1$.",
                "import Mathlib\n\nopen Filter Real Function\nopen scoped Topology\n\ntheorem exercise_3_63b (p : ℝ) "
                "(f : ℕ → ℝ) (hp : p ≤ 1)\n  (h : f = λ (k : ℕ) => (1 : ℝ) / (k * (log k) ^ p)) :\n  ¬ ∃ l, "
                "Tendsto f atTop (𝓝 l) :=sorry"
            ]
        ]
    }

    # Instantiate LLMs
    with open('../api_key.txt', 'r', encoding='utf-8') as f:
        api_key = f.read().rstrip()
    gpt_mini = OpenAILLM(
        name='gpt-mini',
        api_key=api_key,
        model='gpt-4.1-mini'
    )

    for d, fl in [('minif2f', 'Isabelle/HOL'), ('proofnet', 'Lean4')]:
        if d == 'minif2f':
            test_set = MiniF2F(split='test')
        else:
            test_set = ProofNet(split='test')

        afa_gpt = AutoformalizationAgent(
            llm=gpt_mini,
            name='autoformalization gpt-4.1-mini',
            formal_language=fl)

        agent_hard = HardCritiqueAgent(
            name='theorem prover',
            formal_language=fl,
            file_dir=f'../test_results/{d}')
        if fl == 'Isabelle/HOL':
            agent_hard.theorem_prover.verbose = False
            postfix = 'thy'
        else:
            postfix = 'lean'

        fra_gpt = FormalRefinementAgent(
            name='formal refinement with gpt-4.1-mini',
            llm=gpt_mini,
            formal_language=fl)

        res = {'gpt_zs': {},
               'gpt_zs_fr': {},
               'gpt_fs': {},
               'gpt_fs_fr': {}}

        for key, sample in tqdm(zip(test_set.keys, test_set.data), total=len(test_set.keys)):
            informal = sample.informal
            formal, _ = afa_gpt(
                informal_statement=informal)
            res['gpt_zs'][key] = formal

            correctness, error_details = agent_hard(
                formalization=formal,
                file_prefix=f'gpt_zs_{key}')
            if correctness != 'True':
                with open(f'../test_results/{d}/gpt_zs_{key}.{postfix}', 'r', encoding='utf-8') as f:
                    formalization = f.read()
                refinement, _ = fra_gpt(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization=formalization,
                    correctness=correctness,
                    error_details=error_details)
                agent_hard(
                    formalization=refinement,
                    file_prefix=f'gpt_zs_fr_{key}'
                )
            else:
                refinement = formal
                shutil.copy2(f'../test_results/{d}/gpt_zs_{key}.{postfix}',
                             f'../test_results/{d}/gpt_zs_fr_{key}.{postfix}')
                shutil.copy2(f'../test_results/{d}/gpt_zs_{key}.error.log',
                             f'../test_results/{d}/gpt_zs_fr_{key}.error.log')
            res['gpt_zs_fr'][key] = refinement

            formal, _ = afa_gpt(
                informal_statement=informal, informal_formal_pairs=pairs[d])
            res['gpt_fs'][key] = formal
            correctness, error_details = agent_hard(
                formalization=formal,
                file_prefix=f'gpt_fs_{key}')
            if correctness != 'True':
                with open(f'../test_results/{d}/gpt_fs_{key}.{postfix}', 'r', encoding='utf-8') as f:
                    formalization = f.read()
                refinement, _ = fra_gpt(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization=formalization,
                    correctness=correctness,
                    error_details=error_details)
                agent_hard(
                    formalization=refinement,
                    file_prefix=f'gpt_fs_fr_{key}'
                )
            else:
                refinement = formal
                shutil.copy2(f'../test_results/{d}/gpt_fs_{key}.{postfix}',
                             f'../test_results/{d}/gpt_fs_fr_{key}.{postfix}')
                shutil.copy2(f'../test_results/{d}/gpt_fs_{key}.error.log',
                             f'../test_results/{d}/gpt_fs_fr_{key}.error.log')
            res['gpt_fs_fr'][key] = refinement

            for a in res.keys():
                with open(f'../test_results/{d}/{a}.json', 'w', encoding='utf-8') as f:
                    json.dump(res[a], f, ensure_ascii=False, indent=4)

        if fl == 'Isabelle/HOL':
            agent_hard.theorem_prover.terminate()

    deepseekmath = HuggingFaceLLM(
        name='deepseekmath',
        model_id='deepseek-ai/deepseek-math-7b-instruct')
    for d, fl in [('minif2f', 'Isabelle/HOL'), ('proofnet', 'Lean4')]:
        if d == 'minif2f':
            test_set = MiniF2F(split='test')
        else:
            test_set = ProofNet(split='test')

        afa_ds = AutoformalizationAgent(
            llm=deepseekmath,
            name='autoformalization deepseek-math',
            formal_language=fl)

        agent_hard = HardCritiqueAgent(
            name='theorem prover',
            formal_language=fl,
            file_dir=f'../test_results/{d}')
        if fl == 'Isabelle/HOL':
            agent_hard.theorem_prover.verbose = False
            postfix = 'thy'
        else:
            postfix = 'lean'

        fra_gpt = FormalRefinementAgent(
            name='formal refinement with gpt-4.1-mini',
            llm=gpt_mini,
            formal_language=fl)
        fra_ds = FormalRefinementAgent(
            name='formal refinement with deepseek-math',
            llm=deepseekmath,
            formal_language=fl)

        res = {'ds_fs': {},
               'ds_fs_fr': {},
               'ds_fs_fr_gpt': {}}

        for key, sample in tqdm(zip(test_set.keys, test_set.data), total=len(test_set.keys)):
            informal = sample.informal
            formal, _ = afa_ds(
                informal_statement=informal, informal_formal_pairs=pairs[d])
            res['ds_fs'][key] = formal
            correctness, error_details = agent_hard(
                formalization=formal,
                file_prefix=f'ds_fs_{key}')
            if correctness != 'True':
                with open(f'../test_results/{d}/ds_fs_{key}.{postfix}', 'r', encoding='utf-8') as f:
                    formalization = f.read()
                refinement, _ = fra_ds(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization=formalization,
                    correctness=correctness,
                    error_details=error_details)
                agent_hard(
                    formalization=refinement,
                    file_prefix=f'ds_fs_fr_{key}'
                )
            else:
                refinement = formal
                shutil.copy2(f'../test_results/{d}/ds_fs_{key}.{postfix}',
                             f'../test_results/{d}/ds_fs_fr_{key}.{postfix}')
                shutil.copy2(f'../test_results/{d}/ds_fs_{key}.error.log',
                             f'../test_results/{d}/ds_fs_fr_{key}.error.log')

            res['ds_fs_fr'][key] = refinement

            if correctness != 'True':
                with open(f'../test_results/{d}/ds_fs_{key}.{postfix}', 'r', encoding='utf-8') as f:
                    formalization = f.read()
                refinement, _ = fra_gpt(
                    informal_statement=informal,
                    refinement_mode='detailed',
                    formalization=formalization,
                    correctness=correctness,
                    error_details=error_details)
                agent_hard(
                    formalization=refinement,
                    file_prefix=f'ds_fs_fr_gpt_{key}'
                )
            else:
                refinement = formal
                shutil.copy2(f'../test_results/{d}/ds_fs_{key}.{postfix}',
                             f'../test_results/{d}/ds_fs_fr_gpt_{key}.{postfix}')
                shutil.copy2(f'../test_results/{d}/ds_fs_{key}.error.log',
                             f'../test_results/{d}/ds_fs_fr_gpt_{key}.error.log')
            res['ds_fs_fr_gpt'][key] = refinement

            for a in res.keys():
                with open(f'../test_results/{d}/{a}.json', 'w', encoding='utf-8') as f:
                    json.dump(res[a], f, ensure_ascii=False, indent=4)

        if fl == 'Isabelle/HOL':
            agent_hard.theorem_prover.terminate()
