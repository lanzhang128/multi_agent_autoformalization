import os
import json
import argparse
from tqdm import tqdm
import numpy as np
from nltk.translate.bleu_score import corpus_bleu
from nltk.translate.chrf_score import corpus_chrf
from nltk.metrics.distance import edit_distance
from agent import HardCritiqueAgent
from dataset import MiniF2F, ProofNet


def evaluate_bleu(ref_texts, can_texts):
    bleu_references = [[ref.split()] for ref in ref_texts]
    bleu_candidates = [can.split() for can in can_texts]
    return corpus_bleu(bleu_references, bleu_candidates, weights=(0.25, 0.25, 0.25, 0.25))


def evaluate_chrf(ref_texts, can_texts):
    chrf_references = [ref.split() for ref in ref_texts]
    chrf_candidates = [can.split() for can in can_texts]
    return corpus_chrf(chrf_references, chrf_candidates)


def evaluate_ruby(ref_texts, can_texts):
    scores = []
    for ref, can in zip(ref_texts, can_texts):
        sed_score = edit_distance(ref, can)
        scores.append(1 - sed_score / max(len(ref), len(can)))
    return np.mean(scores)


def evaluate_pass(error_logs):
    count = 0
    pass_count = 0

    for log in error_logs:
        correctness = log.split('\n')[0].split()[2]
        count += 1
        if correctness == 'True':
            pass_count += 1
    return pass_count / count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='model evaluation')
    parser.add_argument('--result_json', default='../test_results/minif2f/gpt_zs.json',
                        help='json file that stores results')
    parser.add_argument('-fl', '--formal_language', default='Isabelle/HOL')
    args = parser.parse_args()

    with open(args.result_json, 'r', encoding='utf-8') as f:
        can_json = json.load(f)

    fl = args.formal_language
    if fl not in ['Isabelle/HOL', 'Lean4']:
        raise ValueError

    agent_hard = HardCritiqueAgent(
        name='theorem prover',
        formal_language=fl,
        file_dir=os.path.dirname(args.result_json))

    if 'minif2f' in args.result_json:
        test_set = MiniF2F(split='test')
    else:
        test_set = ProofNet(split='test')

    ref_texts, can_texts, error_logs = [], [], []

    for key, sample in tqdm(zip(test_set.keys, test_set.data), total=len(test_set.keys)):
        if fl == 'Isabelle/HOL':
            ref_texts.append(sample.isabelle)
        else:
            ref_texts.append(sample.lean)
        can_texts.append(can_json[key])

        if not os.path.exists(args.result_json[:-5] + f'_{key}.error.log'):
            agent_hard(formalization=can_json[key], file_prefix=os.path.basename(args.result_json)[:-5] + f'_{key}')

        with open(args.result_json[:-5] + f'_{key}.error.log', 'r', encoding='utf-8') as f:
            error_logs.append(f.read())

    if fl == 'Isabelle/HOL':
        agent_hard.theorem_prover.terminate()

    print(f'bleu: {evaluate_bleu(ref_texts, can_texts)}')
    print(f'chrf: {evaluate_chrf(ref_texts, can_texts)}')
    print(f'ruby: {evaluate_ruby(ref_texts, can_texts)}')
    print(f'pass: {evaluate_pass(error_logs)}')
