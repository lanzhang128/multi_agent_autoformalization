import os
import json
import re

if __name__ == '__main__':
    for split in ['valid', 'test']:
        informal_dir = f'miniF2F/informal/{split}'
        isabelle_dir = f'miniF2F/isabelle/{split}'
        lean_all = {}
        with open(f'miniF2F/lean4/{split}.jsonl', 'r', encoding='utf-8') as f:
            for data in f.readlines():
                data = json.loads(data)
                lean_all[data['id']] = data['formal_statement']

        id = 0
        res = {}
        for root, _, files in os.walk(informal_dir):
            for file in files:
                with open(os.path.join(informal_dir, file), 'r', encoding='utf-8') as f:
                    informal = json.load(f)['informal_statement']
                with open(os.path.join(isabelle_dir, file[:-4] + 'thy'), 'r', encoding='utf-8') as f:
                    isabelle = f.read()

                isabelle = re.findall(f'theory.*end', isabelle, flags=re.DOTALL)[0]
                isabelle = re.sub(f'(proof|using).*end', 'sorry\n\nend', isabelle, flags=re.DOTALL)
                isabelle = isabelle.replace('\"HOL-Analysis.Analysis\"', '')
                isabelle = isabelle.replace('\"Symmetric_Polynomials.Vieta\"', '')
                lean = 'import Mathlib\n\nopen BigOperators Real Nat Topology\n\n' + lean_all[file[:-5]]

                res[str(id)] = {
                    'id': id,
                    'source': file[:-5],
                    'latex': informal,
                    'isabelle': isabelle,
                    'lean4': lean
                }
                id += 1

        with open(f'minif2f_{split}.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
