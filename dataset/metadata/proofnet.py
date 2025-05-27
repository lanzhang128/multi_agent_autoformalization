import json
from tqdm import tqdm
from agent import HardCritiqueAgent


if __name__ == '__main__':
    agent = HardCritiqueAgent(
        name='theorem prover',
        formal_language='Lean4',
        file_dir='../test_results')

    valid = {}
    test = {}
    with open('proofnet.jsonl', 'r', encoding='utf-8') as f:
        for data in tqdm(f.readlines()):
            data = json.loads(data)
            res = {
                'source': data['name'],
                'latex': data['informal_prefix'][4:-3],
                'lean4': data['header'] + data['formal_statement'] + 'sorry'}

            correctness, error_details = agent(
                formalization=res['lean4'],
                file_prefix=res['source'])

            if correctness == 'True':
                if data['split'] == 'valid':
                    i = len(valid)
                    res['id'] = i
                    valid[str(i)] = res
                else:
                    i = len(test)
                    res['id'] = i
                    test[str(i)] = res
            else:
                print(res['source'])

            with open('proofnet_valid.json', 'w', encoding='utf-8') as f:
                json.dump(valid, f, ensure_ascii=False, indent=4)
            with open('proofnet_test.json', 'w', encoding='utf-8') as f:
                json.dump(test, f, ensure_ascii=False, indent=4)
