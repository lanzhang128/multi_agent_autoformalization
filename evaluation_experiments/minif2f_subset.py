import os
import json
import random


if __name__ == '__main__':
    informal_dir = '../miniF2F/informal/test'
    formal_dir = '../miniF2F/isabelle/test'
    random.seed(0)
    id = 0
    res = {}
    for root, _, files in os.walk(informal_dir):
        files = random.sample(files, 50)
        for file in files:
            with open(os.path.join(informal_dir, file), 'r', encoding='utf-8') as f:
                informal = json.load(f)['informal_statement']
            with open(os.path.join(formal_dir, file[:-4] + 'thy'), 'r', encoding='utf-8') as f:
                formal = f.read()
            res[str(id)] = {
                'id': id,
                'source': file,
                'latex': informal,
                'formal': formal,
            }
            id += 1

    with open('minif2f_subset_test.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
