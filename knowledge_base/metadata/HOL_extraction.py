import os
import json
import re


def parse_thy_file(file_name):
    assert file_name[-4:] == '.thy'

    keywords = ['declare', 'syntax', 'ML', 'instance', 'statespace',
                'typedef', 'type_synonym', 'definition', 'abbreviation',
                'fun', 'function', 'inductive', 'class', 'locale',
                'sublocale', 'lemma', 'corollary', 'theorem']

    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.read()

    comments = []
    start = 0
    while start < len(lines) - 1:
        if lines[start:start + 2] == '(*':
            count = 1
            end = start + 2
            while end < len(lines) - 1 and count > 0:
                if lines[end:end + 2] == '*)':
                    count -= 1
                    end = end + 2
                elif lines[end:end + 2] == '(*':
                    count += 1
                    end = end + 2
                else:
                    end = end + 1
            comments.append((start, end))
            start = end
        start += 1

    new_lines = ''
    start = 0
    for (l, r) in comments:
        new_lines += lines[start:l]
        start = r
    new_lines += lines[start:]

    dirname = os.path.dirname(file_name)
    prefix = dirname[dirname.find('HOL'):]
    if prefix != 'HOL':
        if 'HOLCF' in prefix:
            prefix = prefix[prefix.find('HOLCF'):]
        prefix = prefix.replace('/', '-').replace('\\', '-')
    source = prefix + '.' + os.path.basename(file_name)[:-4]

    imports = re.findall('imports.*?begin', new_lines, flags=re.DOTALL)
    imports = imports[0][7:-5].replace('\n', ' ').split()
    abs_imports = []
    for thy in imports:
        if '.' in thy:
            abs_imports.append(thy.replace('\"', ''))
        else:
            abs_imports.append(prefix + '.' + thy)

    lines = [_ + '\n' for _ in new_lines.split('\n')]

    chunks = []
    start = 0
    while start < len(lines):
        temp = lines[start].split()
        if temp:
            if temp[0] in keywords or lines[start][:4] == 'text':
                end = start + 1
                while end < len(lines):
                    if lines[end].rstrip().replace(' ', '') == '':
                        break
                    elif lines[end].split()[0] in keywords:
                        break
                    elif lines[end][:4] == 'text':
                        break
                    else:
                        end += 1
                chunks.append(''.join(lines[start:end]))
                start = end
            else:
                start = start + 1
        else:
            start = start + 1

    items = []
    for i in range(len(chunks)):
        temp = chunks[i].split()
        if temp[0] in keywords[5:]:
            item = {'type': temp[0],
                    'text': '',
                    'statement': '',
                    'assumes': '',
                    'proof': '',
                    'using': [],
                    'abs_imports': abs_imports,
                    'source': source}
            if i > 0:
                if chunks[i - 1][:4] == 'text':
                    item['text'] = chunks[i - 1]

            if 'assumes' in chunks[i]:
                if 'shows' in chunks[i]:
                    item['assumes'] = chunks[i][chunks[i].find('assumes'):chunks[i].find('shows')]
                elif 'obtains' in chunks[i]:
                    item['assumes'] = chunks[i][chunks[i].find('assumes'):chunks[i].find('obtains')]
                else:
                    item['assumes'] = chunks[i][chunks[i].find('assumes'):]

            for s in re.findall('using.*?by', chunks[i], flags=re.DOTALL):
                s = s[:-2]
                s = s.replace('\n', '')
                s = s.replace('unfolding', '')
                s = s.replace('using', '')
                s = s.split()
                item['using'] += s
            item['using'] = list(dict.fromkeys(item['using']))

            if 'proof' in chunks[i] and 'qed' in chunks[i]:
                item['statement'] = chunks[i][:chunks[i].find('proof')]
                item['proof'] = chunks[i][chunks[i].find('proof'):]
            else:
                if 'using' in chunks[i]:
                    item['statement'] = chunks[i][:chunks[i].find('using')]
                    item['proof'] = chunks[i][chunks[i].find('using'):]
                else:
                    item['statement'] = chunks[i]

            items.append(item)
    return items


if __name__ == '__main__':
    data_id = 0
    json_dic = {}
    for root, _, files in os.walk('../../../Isabelle2024/src/HOL'):
        files.sort()
        for file in files:
            if file[-4:] == '.thy':
                items = parse_thy_file(os.path.join(root, file))
                for item in items:
                    item['id'] = data_id
                    json_dic[f'{data_id}'] = item
                    data_id += 1

    with open(os.path.join(os.path.dirname(__file__), 'Isabelle_HOL.json'), 'w', encoding='utf-8') as f:
        json.dump(json_dic, f, ensure_ascii=False, indent=4)
