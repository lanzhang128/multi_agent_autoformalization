import os
import json
import argparse
from tqdm import tqdm
from nltk.translate.bleu_score import corpus_bleu
from agent import HardCritiqueAgent


def evaluate_bleu(ref_texts, can_texts):
    score_dic = {}
    bleu_references = [[ref.split()] for ref in ref_texts]
    bleu_candidates = [can.split() for can in can_texts]
    score_dic['BLEU-1'] = corpus_bleu(bleu_references, bleu_candidates, weights=(1, 0, 0, 0))
    score_dic['BLEU-2'] = corpus_bleu(bleu_references, bleu_candidates, weights=(0.5, 0.5, 0, 0))
    score_dic['BLEU-4'] = corpus_bleu(bleu_references, bleu_candidates, weights=(0.25, 0.25, 0.25, 0.25))
    return score_dic


def evaluate_pass(agent, can_json):
    count = 0
    pass_count = 0

    for key in tqdm(can_json.keys()):
        if 'correctness' in can_json[key]:
            correctness = can_json[key]['correctness']
        else:
            correctness, error_details = agent(
                formalization=can_json[key]['formalization'],
                file_prefix='test')

        count += 1
        if correctness == 'True':
            pass_count += 1
    return {'Pass Count': pass_count, 'Pass Rate': pass_count / count}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='model evaluation')
    parser.add_argument('--ref_json', default='minif2f_subset_test.json',
                        help='json file that stores reference data')
    parser.add_argument('--result_json', default='self_improving.json',
                        help='json file that stores results')
    parser.add_argument('--key', default='zero-shot')
    args = parser.parse_args()

    with open(args.ref_json, 'r', encoding='utf-8') as f:
        ref_json = json.load(f)

    with open(args.result_json, 'r', encoding='utf-8') as f:
        can_json = json.load(f)[args.key]

    ref_formal, can_formal = [], []

    for key in can_json.keys():
        formal = ref_json[key]['formal']
        ref_formal.append(formal[formal.find('theory'):])
        can_formal.append(can_json[key]['formalization'])

    score_dic = evaluate_bleu(ref_formal, can_formal)

    agent_hard = HardCritiqueAgent(
        name='theorem prover',
        formal_language='Isabelle/HOL',
        file_dir='../test_results',
    )
    agent_hard.theorem_prover.verbose = False

    score_dic.update(evaluate_pass(agent_hard, can_json))
    print(score_dic)
    agent_hard.theorem_prover.terminate()

