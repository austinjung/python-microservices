import datetime
import pprint
import re
import string
# from memory_profiler import profile
import tracemalloc
from collections import defaultdict

import jsonpickle
from pyciiml.utils.file_utils import get_basename, write_json

tracemalloc.start()
added_terminology = set()

suppress_words_patterns = [
    r'</sub>', r'<sub>', r'</sup>', r'<sup>',
    r'\(', r'\)', r'{', r'}', r'[', r']',
    r'<', r'>', r'\^', r'same as '
]
suppress_words = r'|'.join(map(r'(?:{})'.format, suppress_words_patterns))


class IrregVariant(defaultdict):
    def __missing__(self, key):
        if key in self:
            return self[key]
        else:
            return key

    def __setitem__(self, key, value):
        if key == value:
            return
        super().__setitem__(key, value)


class TokenDictionary(dict):
    def __init__(self):
        self.dic_list = []
        self.next_index = 0  # next index of dic list
        super().__init__()

    def __setitem__(self, token, value=None):
        """ Add self[token] and set value to index. """
        if token in self:
            return
        if getattr(self, 'dic_list', None) is None or getattr(self, 'next_index', None) is None:
            return
        if isinstance(value, int) and token == self.dic_list[value]:
            super().__setitem__(token, value)
            return
        super().__setitem__(token, self.next_index)
        self.dic_list.append(token)
        self.next_index += 1

    def add_tokens(self, tokens):
        for token in tokens:
            self.__setitem__(token)

    def get_or_add_token_dic(self, token):
        if token not in self:
            self.__setitem__(token)
        return self[token]


class AustinSimpleParser:
    """
    Austin's simple parser which provide build simple named entities with tags and parse
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.children_tries = {}
        self.tags = {}
        if parent is None:
            self.token_dict = TokenDictionary()
            self.irregular_variant = IrregVariant()
        else:
            self.token_dict = self._get_top().token_dict
            self.irregular_variant = self._get_top().irregular_variant

    def _add_next_token(self, next_token):
        next_token_dic = self.token_dict.get_or_add_token_dic(next_token)
        if next_token_dic not in self.children_tries:
            self.children_tries[next_token_dic] = AustinSimpleParser(parent=self)
        return self.children_tries[next_token_dic]

    def _update_tags(self, new_tags):
        for key, value in new_tags.items():
            if value is None:
                if key in self.tags:
                    self.tags.pop(key)
            elif key in ['cat', 'position', 't2']:
                if self.tags.get(key) and value not in self.tags[key]:
                    self.tags[key].append(value)
                else:
                    self.tags[key] = [value]
            else:
                self.tags[key] = value

    def _add_next_tokens(self, tokens, tags=None):
        if len(tokens) > 0:
            self._add_next_token(tokens[0])._add_next_tokens(tokens[1:], tags)
        else:
            if tags is None:
                tags = {}
            self._update_tags(tags)

    def _get_top(self):
        if self.parent is None:
            return self
        return self.parent._get_top()

    def _get_tries(self, tokens, start_idx, idx):
        if idx >= len(tokens):
            return [(' '.join(tokens[start_idx:]), self.tags)]
        token_dic_id = self.token_dict.get(tokens[idx], None)
        if token_dic_id in self.children_tries:
            return self.children_tries[token_dic_id]._get_tries(tokens, start_idx, idx + 1)
        if token_dic_id:
            new_tokens = [(' '.join(tokens[start_idx: idx]), self.tags)]
            new_tokens.extend(self._get_top()._parse_tokens(tokens, idx))
            return new_tokens
        variants = self.get_variants(tokens[idx])
        if variants is None:
            new_tokens = [(' '.join(tokens[start_idx: idx]), self.tags)]
            new_tokens.extend(self._get_top()._parse_tokens(tokens, idx))
            return new_tokens
        if isinstance(variants, list):
            new_tokens = tokens[:idx] + (variants + tokens[idx + 1:])
            token_dic_id = self.token_dict.get(new_tokens[idx], None)
            if token_dic_id in self.children_tries:
                return self.children_tries[token_dic_id]._get_tries(new_tokens, start_idx, idx + 1)
        tokens[idx] = variants
        token_dic_id = self.token_dict.get(tokens[idx], None)
        return self.children_tries[token_dic_id]._get_tries(tokens, start_idx, idx + 1)

    def build_trie(self, words, tags=None):
        tokens = [token.lower() for token in words.split()]
        self._add_next_tokens(tokens, tags)

    def get_variants(self, token):
        variants = None
        if token in ['', None]:
            return variants
        elif token in string.punctuation:
            return variants
        elif token[-2:] == "'s" and token[:-2] in self.token_dict and len(token) > 2:
            variants = token[:-2]
        elif token[-2:] == "s'" and token[:-1] in self.token_dict and len(token) > 2:
            variants = token[:-1]
        elif token[-1:] == "s" and token[:-1] in self.token_dict and len(token) > 1:
            variants = token[:-1]
        elif token[-1:] == "d" and token[:-1] in self.token_dict and len(token) > 1:
            variants = token[:-1]
        elif token[-2:] == "es" and token[:-2] in self.token_dict and len(token) > 2:
            variants = token[:-2]
        elif token[-2:] == "ed" and token[:-2] in self.token_dict and len(token) > 2:
            variants = token[:-2]
        elif token[-2:] == "er" and token[:-2] in self.token_dict and len(token) > 2:
            variants = token[:-2]
        elif token[-3:] == "est" and token[:-3] in self.token_dict and len(token) > 3:
            variants = token[:-3]
        elif token[-1:] in string.punctuation:
            variants = [token[:-1], token[-1:]]
        elif token[:1] in string.punctuation:
            variants = [token[:1], token[1:]]
        return variants

    def _parse_tokens(self, tokens, idx):
        if idx >= len(tokens):
            return []
        token_dic_id = self.token_dict.get(tokens[idx], None)
        if token_dic_id in self.children_tries:
            return self.children_tries[token_dic_id]._get_tries(tokens, idx, idx + 1)
        if token_dic_id:
            new_tokens = [(tokens[idx], {})]
            new_tokens.extend(self._get_top()._parse_tokens(tokens, idx + 1))
            return new_tokens
        variants = self.get_variants(tokens[idx])
        if variants is None:
            new_tokens = [(tokens[idx], {})]
            new_tokens.extend(self._get_top()._parse_tokens(tokens, idx + 1))
            return new_tokens
        if isinstance(variants, list):
            new_tokens = tokens[:idx] + (variants + tokens[idx + 1:])
            token_dic_id = self.token_dict.get(new_tokens[idx], None)
            if token_dic_id in self.children_tries:
                return self.children_tries[token_dic_id]._get_tries(new_tokens, idx, idx + 1)
        tokens[idx] = variants
        token_dic_id = self.token_dict.get(tokens[idx], None)
        return self.children_tries[token_dic_id]._get_tries(tokens, idx, idx + 1)

    def parse_words(self, words):
        tokens = [token.lower() for token in words.split()]
        return self._parse_tokens(tokens, 0)

    def fix_token_dict(self):
        dic_set = set(enumerate(self.token_dict.dic_list))
        token_set = set([(idx, key) for key, idx in self.token_dict.items()])
        for idx, key in dic_set.difference(token_set):
                self.token_dict[key] = idx


def initialize_lexicon():
    return {
        'base': None,
        'cat': None,  # aux, modal, pron, compl, det --> skip, noun(+), adj, adv, verb, prep
        'position': [],
        'irreg_variants': [],
        'variants': [],
        'spelling_variant': [],
        'trademark': None
    }


global_specialist_lexicon_parser = AustinSimpleParser()
global_specialist_lexicon_parser_pickle = "global_specialist_lexicon_parser.pickle"


# @profile()
def process_line_of_special_lexicon(line, lexicon):
    if line.startswith('{base='):
        lexicon['base'] = line.replace('{base=', '').replace('\n', '')
    elif line.startswith('\tcat='):
        lexicon['cat'] = line.replace('\tcat=', '').replace('\n', '')
    elif line.startswith('\tposition='):
        lexicon['position'].append(line.replace('\tposition=', '').replace('\n', ''))
    elif line.startswith('\tvariants=irreg|'):
        lexicon['irreg_variants'].extend(line.replace('\tvariants=irreg|', '').replace('|\n', '').split('|')[1:])
    elif line.startswith('\tvariants='):
        lexicon['variants'].append(line.replace('\tvariants=', '').replace('\n', ''))
    elif line.startswith('spelling_variant='):
        lexicon['spelling_variant'].append(line.replace('spelling_variant=', '').replace('\n', ''))
    elif line.startswith('\ttrademark='):
        lexicon['trademark'] = line.replace('\ttrademark=', '').replace('\n', '')
    elif line.startswith('}'):
        # if cat in ['adj', 'adv', 'verb', 'pre'] or (cat == 'noun' and len(base.split()) > 1):
        global global_specialist_lexicon_parser
        base = lexicon.pop('base')
        irreg_variants = lexicon.pop('irreg_variants')
        spelling_variant = lexicon.pop('spelling_variant')
        trademark = lexicon.pop('trademark')

        global_specialist_lexicon_parser.build_trie(base, tags=lexicon)
        if len(irreg_variants):
            for variant in irreg_variants:
                global_specialist_lexicon_parser.build_trie(variant, tags=lexicon)
        if len(spelling_variant):
            for variant in spelling_variant:
                global_specialist_lexicon_parser.build_trie(variant, tags=lexicon)
        if trademark:
            global_specialist_lexicon_parser.build_trie(trademark, tags=lexicon)
        return initialize_lexicon()
    return lexicon


def save_specialist_lexicon_parser():
    global global_specialist_lexicon_parser, global_specialist_lexicon_parser_pickle
    with open(global_specialist_lexicon_parser_pickle, mode='w', encoding='utf-8', errors='replace') as pickle:
        pickle.write(jsonpickle.encode(global_specialist_lexicon_parser, keys=True))


# @profile()
def build_specialist_lexicon_parser():
    global global_specialist_lexicon_parser
    for punct in string.punctuation:
        global_specialist_lexicon_parser.build_trie(punct, tags={'cat': 'punct'})
    with open('LEXICON', mode='r', encoding='utf-8', errors='replace') as lexicon_file:
        lexicon = initialize_lexicon()
        for line in lexicon_file:
            lexicon = process_line_of_special_lexicon(line, lexicon)
    # save_specialist_lexicon_parser()


def normalize_and_expand_to_build_terminology(line):
    """
    After building terminology with this method, we need to skip punct and conj to build med-embedding
    """
    lower_line = line.lower()
    suppressed_line = re.sub(suppress_words, '', lower_line).strip()
    lines = [suppressed_line]
    if ', ' in suppressed_line:
        lines = [suppressed_line.replace(', ', ' , ')]  # make ', ' as separate token
        for conj in [' and ', ' or ', ' and/or ']:
            if conj in suppressed_line:
                lines.append(suppressed_line.replace(', ', conj))
                lines.append(suppressed_line.replace(', ', ' ').replace(conj, ' '))
                break
        if len(lines) == 1:  # Has no conj
            lines.append(suppressed_line.replace(', ', ' '))  # append without ', '

    for token in ['on examination', 'o/e']:
        if token in suppressed_line:
            suppressed_line = suppressed_line.replace(token, '')
            if suppressed_line.strip() != '' and ' - ' not in suppressed_line:
                lines.append(suppressed_line.strip())

    if ' - ' in suppressed_line:  # It may have full name of acronym
        split_lines = suppressed_line.split(' - ')
        if split_lines[0].strip() != '':
            lines.append(split_lines[0].strip())
        if ' '.join(split_lines[1:]).strip() != '':
            lines.append(' '.join(split_lines[1:]).strip())

    return lines


def normalize_line_of_terminology(line):
    line = line.replace("\t\t", "\t")
    try:
        code, attr, desc, terminology_of_entry_type = line.split("\t")
        generic_code = None
        generic_terminology = None
    except ValueError:
        code, attr, desc, generic_code, generic_terminology, terminology_of_entry_type = line.split("\t")
    terminology_of_entry_type = terminology_of_entry_type.replace('\n', '')
    return code, attr, desc, generic_code, generic_terminology, terminology_of_entry_type


def build_med_terminology(terminology_file_path, entity_name=None):
    global added_terminology, split_characters, global_specialist_lexicon_parser
    if entity_name is None:
        entity_name = get_basename(terminology_file_path).replace('.txt', '')
    with open(terminology_file_path, 'r', encoding='utf-8', errors='replace') as fp:
        for line in fp:
            code, attr, desc, generic_code, generic_terminology, terminology_of_entry_type = \
                normalize_line_of_terminology(line)
            if attr in ['SY', 'PT']:
                tags = {
                    'cat': 'noun',
                    't2': {
                        'code': code,
                        'entity': entity_name
                    }
                }
                terminologies = normalize_and_expand_to_build_terminology(desc)
                for terminology in terminologies:
                    if (code, terminology) not in added_terminology:
                        global_specialist_lexicon_parser.build_trie(terminology, tags)
                        added_terminology.add((code, terminology))
                if generic_code and generic_terminology:
                    terminology = generic_terminology.strip()
                    if (generic_code, terminology) not in added_terminology:
                        tags['t2_code'] = generic_code
                        global_specialist_lexicon_parser.build_trie(terminology, tags)
                        added_terminology.add((generic_code, terminology))
    save_specialist_lexicon_parser()
    write_json(list(added_terminology), '{0}_added.json'.format(entity_name))


# @profile
def read_specialist_lexicon_parser():
    global global_specialist_lexicon_parser, global_specialist_lexicon_parser_pickle
    global_specialist_lexicon_parser = AustinSimpleParser()
    with open(global_specialist_lexicon_parser_pickle, mode='r', encoding='utf-8', errors='replace') as pickle:
        global_specialist_lexicon_parser = jsonpickle.decode(pickle.read(), keys=True)
    global_specialist_lexicon_parser.fix_token_dict()
    return global_specialist_lexicon_parser


# @profile
def parse_test():
    print(datetime.datetime.now())
    global global_specialist_lexicon_parser
    global_specialist_lexicon_parser = read_specialist_lexicon_parser()
    specialist_lexicon_parser = global_specialist_lexicon_parser
    print(datetime.datetime.now())
    parsed8 = specialist_lexicon_parser.parse_words('I had a breast cancer treatments and cancer test')
    pprint.pprint(parsed8)
    parsed8 = specialist_lexicon_parser.parse_words('I had Chronic idiopathic hemolytic anemia.')
    pprint.pprint(parsed8)
    parsed8 = specialist_lexicon_parser.parse_words('I had Chronic idiopathic hemolytic anemia C.A.P.')
    pprint.pprint(parsed8)
    parsed8 = specialist_lexicon_parser.parse_words('I had a Neoplasm of uncertain behavior of left upper lobe of lung')
    pprint.pprint(parsed8)
    parsed8 = specialist_lexicon_parser.parse_words('spinocerebellar ataxia type 14')
    pprint.pprint(parsed8)


if __name__ == '__main__':
    # print(datetime.datetime.now())
    # build_specialist_lexicon_parser()
    # print(datetime.datetime.now())
    # print('----------------------')
    # build_med_terminology('terminology/adverseReaction.txt')
    # print('----------------------')
    print(datetime.datetime.now())
    parse_test()
    print(datetime.datetime.now())
    # build_med_terminology('terminology/biomarker.txt')
    # build_med_terminology('terminology/chemotherapy.txt')
    print(datetime.datetime.now())
    print('----------------------')
    print("Current: %d, Peak %d" % tracemalloc.get_traced_memory())
