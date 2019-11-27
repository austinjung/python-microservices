from collections import defaultdict


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
        if parent is None:
            self.token_dict = TokenDictionary()
        else:
            self.token_dict = self.get_top().token_dict

    def add_next_token(self, next_token):
        next_token_dic = self.token_dict.get_or_add_token_dic(next_token)
        if next_token_dic not in self.children_tries:
            self.children_tries[next_token_dic] = AustinSimpleParser(parent=self)
        return self.children_tries[next_token_dic]

    def add_next_tokens(self, tokens):
        if len(tokens) > 0:
            self.add_next_token(tokens[0]).add_next_tokens(tokens[1:])

    def build_trie(self, words):
        tokens = [token.lower() for token in words.split()]
        self.add_next_tokens(tokens)

    def get_top(self):
        if self.parent is None:
            return self
        return self.parent.get_top()

    def get_tries(self, tokens, start_idx, idx):
        if idx >= len(tokens):
            return [' '.join(tokens[start_idx:])]
        token_dict = self.token_dict.get(tokens[idx], None)
        if token_dict in self.children_tries:
            return self.children_tries[token_dict].get_tries(tokens, start_idx, idx + 1)
        new_tokens = [' '.join(tokens[start_idx: idx])]
        new_tokens.extend(self.parse_tokens(tokens, idx))
        return new_tokens

    def parse_tokens(self, tokens, idx):
        if idx >= len(tokens):
            return []
        token_dict = self.token_dict.get(tokens[idx], None)
        if token_dict in self.children_tries:
            return self.children_tries[token_dict].get_tries(tokens, idx, idx + 1)
        new_tokens = [tokens[idx]]
        new_tokens.extend(self.parse_tokens(tokens, idx + 1))
        return new_tokens

    def parse_words(self, words):
        tokens = [token.lower() for token in words.split()]
        return self.parse_tokens(tokens, 0)


if __name__ == '__main__':
    irreg_variants = IrregVariant()
    irreg_variants['saw'] = 'see'
    irreg_variants['seen'] = 'see'
    irreg_variants['see'] = 'see'
    assert(irreg_variants['saw'] == 'see')
    assert(irreg_variants['seen'] == 'see')
    assert(irreg_variants['see'] == 'see')
    token_dict = TokenDictionary()
    token_dict.add_tokens(['breast', 'cancer', 'treatment'])
    token_dict['right'] = True
    assert(token_dict['breast'] == 0)
    assert(token_dict['cancer'] == 1)
    assert(token_dict['treatment'] == 2)
    assert(token_dict['right'] == 3)
    specialist_lexicon = AustinSimpleParser()
    specialist_lexicon.build_trie('cancer')
    specialist_lexicon.build_trie('breast cancer')
    specialist_lexicon.build_trie('right breast cancer')
    specialist_lexicon.build_trie('breast cancer treatment')
    parsed1 = specialist_lexicon.parse_words('cancer')
    assert(parsed1 == ['cancer'])
    parsed2 = specialist_lexicon.parse_words('breast cancer')
    assert(parsed2 == ['breast cancer'])
    parsed3 = specialist_lexicon.parse_words('a breast cancer')
    assert(parsed3 == ['a', 'breast cancer'])
    parsed4 = specialist_lexicon.parse_words('have a breast cancer')
    assert(parsed4 == ['have', 'a', 'breast cancer'])
    parsed5 = specialist_lexicon.parse_words('I have a breast cancer')
    assert(parsed5 == ['i', 'have', 'a', 'breast cancer'])
    parsed6 = specialist_lexicon.parse_words('I have a breast cancer treatment')
    assert(parsed6 == ['i', 'have', 'a', 'breast cancer treatment'])
    parsed7 = specialist_lexicon.parse_words('I have a breast cancer treatments')
    assert(parsed7 == ['i', 'have', 'a', 'breast cancer', 'treatments'])
    assert(specialist_lexicon.token_dict == list(specialist_lexicon.children_tries.values())[0].token_dict)