from collections import defaultdict

from memory_profiler import profile


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
            elif key in ['cat', 'position']:
                if self.tags.get(key):
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
        new_tokens = [(' '.join(tokens[start_idx: idx]), self.tags)]
        new_tokens.extend(self._get_top()._parse_tokens(tokens, idx))
        return new_tokens

    def build_trie(self, words, tags=None):
        tokens = [token.lower() for token in words.split()]
        self._add_next_tokens(tokens, tags)

    def _parse_tokens(self, tokens, idx):
        if idx >= len(tokens):
            return []
        token_dic_id = self.token_dict.get(tokens[idx], None)
        if token_dic_id in self.children_tries:
            return self.children_tries[token_dic_id]._get_tries(tokens, idx, idx + 1)
        new_tokens = [(tokens[idx], {})]
        new_tokens.extend(self._get_top()._parse_tokens(tokens, idx + 1))
        return new_tokens

    def parse_words(self, words):
        tokens = [token.lower() for token in words.split()]
        return self._parse_tokens(tokens, 0)


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
        return initialize_lexicon(), 1
    return lexicon, 0


# @profile()
def build_specialist_lexicon_parser():
    with open('LEXICON', mode='r', encoding='utf-8', errors='replace') as lexicon_file:
        lexicon_number = 0
        lexicon = initialize_lexicon()
        for line in lexicon_file:
            lexicon, added_lexicon = process_line_of_special_lexicon(line, lexicon)
            lexicon_number += added_lexicon

    print(lexicon_number)


if __name__ == '__main__':
    build_specialist_lexicon_parser()
