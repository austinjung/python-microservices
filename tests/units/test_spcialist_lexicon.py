import jsonpickle

from microservices.specialist_lexicon.build_spcialist_lexicon import AustinSimpleParser, IrregVariant, TokenDictionary

global_specialist_lexicon_parser = "global_specialist_lexicon_parser.pickle"


def test_irreg_variants():
    irreg_variants = IrregVariant()
    irreg_variants['saw'] = 'see'
    irreg_variants['seen'] = 'see'
    irreg_variants['see'] = 'see'
    assert (irreg_variants['saw'] == 'see')
    assert (irreg_variants['seen'] == 'see')
    assert (irreg_variants['see'] == 'see')


def test_token_dictionary():
    token_dict = TokenDictionary()
    token_dict.add_tokens(['breast', 'cancer', 'treatment'])
    token_dict['right'] = True
    assert (token_dict['breast'] == 0)
    assert (token_dict['cancer'] == 1)
    assert (token_dict['treatment'] == 2)
    assert (token_dict['right'] == 3)


def test_austin_simple_parser():
    specialist_lexicon = AustinSimpleParser()
    # build dictionary with tags
    specialist_lexicon.build_trie('cancer', tags={'snomed_tag': 'disorder'})
    specialist_lexicon.build_trie('breast cancer', tags={'snomed_tag': 'disorder'})
    specialist_lexicon.build_trie('breast', tags={'cat': 'noun', 'position': ['noun_position', 'position1']})
    specialist_lexicon.build_trie('right breast cancer', tags={'snomed_tag': 'disorder'})
    specialist_lexicon.build_trie('breast cancer treatment', tags={'snomed_tag': 'treatment'})
    # Parse sentence
    parsed1 = specialist_lexicon.parse_words('cancer')
    assert (parsed1 == [('cancer', {'snomed_tag': 'disorder'})])
    parsed11 = specialist_lexicon.parse_words('breast')
    assert (parsed11 == [('breast', {'cat': ['noun'], 'position': [['noun_position', 'position1']]})])
    parsed2 = specialist_lexicon.parse_words('breast cancer')
    assert (parsed2 == [('breast cancer', {'snomed_tag': 'disorder'})])
    parsed3 = specialist_lexicon.parse_words('a breast cancer')
    assert (parsed3 == [('a', {}), ('breast cancer', {'snomed_tag': 'disorder'})])
    parsed4 = specialist_lexicon.parse_words('have a breast cancer')
    assert (parsed4 == [('have', {}), ('a', {}), ('breast cancer', {'snomed_tag': 'disorder'})])
    parsed5 = specialist_lexicon.parse_words('I have a breast cancer')
    assert (parsed5 == [('i', {}), ('have', {}), ('a', {}), ('breast cancer', {'snomed_tag': 'disorder'})])
    parsed6 = specialist_lexicon.parse_words('I have a breast cancer treatment')
    assert (parsed6 == [('i', {}), ('have', {}), ('a', {}), ('breast cancer treatment', {'snomed_tag': 'treatment'})])
    parsed7 = specialist_lexicon.parse_words('I have a breast cancer treatments')
    assert (parsed7 == [('i', {}), ('have', {}), ('a', {}), ('breast cancer', {'snomed_tag': 'disorder'}),
                        ('treatments', {})])
    parsed8 = specialist_lexicon.parse_words('I had a breast cancer treatments and cancer test')
    assert (parsed8 == [('i', {}), ('had', {}), ('a', {}), ('breast cancer', {'snomed_tag': 'disorder'}),
                        ('treatments', {}), ('and', {}), ('cancer', {'snomed_tag': 'disorder'}), ('test', {})])
    assert (specialist_lexicon.token_dict == list(specialist_lexicon.children_tries.values())[0].token_dict)
    global global_specialist_lexicon_parser
    with open(global_specialist_lexicon_parser, mode='w', encoding='utf-8', errors='replace') as pickle:
        pickle.write(jsonpickle.encode(specialist_lexicon, keys=True))


def test_austin_simple_parser_update_tags():
    global global_specialist_lexicon_parser
    with open(global_specialist_lexicon_parser, mode='r', encoding='utf-8', errors='replace') as pickle:
        specialist_lexicon = jsonpickle.decode(pickle.read(), keys=True)
    # Tags update
    specialist_lexicon.build_trie('cancer', tags={'entity_type': 'disease', 'pipeline': 'cancer'})
    specialist_lexicon.build_trie('breast', tags={'cat': 'verb', 'position': ['verb_position', 'position2']})
    specialist_lexicon.build_trie('breast cancer', tags={'entity_type': 'disease', 'pipeline': 'cancer'})
    specialist_lexicon.build_trie('right breast cancer', tags={'entity_type': 'disease', 'pipeline': 'cancer'})
    specialist_lexicon.build_trie('breast cancer treatment', tags={'snomed_tag': None, 'entity_type': 'chemotherapy'})
    # Parse sentence again
    parsed1 = specialist_lexicon.parse_words('cancer')
    assert (parsed1 == [('cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'})])
    parsed11 = specialist_lexicon.parse_words('breast')
    assert (parsed11 == [('breast', {'cat': ['noun', 'verb'], 'position': [['noun_position', 'position1'],
                                                                           ['verb_position', 'position2']]})])
    parsed2 = specialist_lexicon.parse_words('breast cancer')
    assert (parsed2 == [('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'})])
    parsed3 = specialist_lexicon.parse_words('a breast cancer')
    assert (parsed3 == [('a', {}),
                        ('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'})])
    parsed4 = specialist_lexicon.parse_words('have a breast cancer')
    assert (parsed4 == [('have', {}), ('a', {}),
                        ('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'})])
    parsed5 = specialist_lexicon.parse_words('I have a breast cancer')
    assert (parsed5 == [('i', {}), ('have', {}), ('a', {}),
                        ('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'})])
    parsed6 = specialist_lexicon.parse_words('I have a breast cancer treatment')
    assert (parsed6 == [('i', {}), ('have', {}), ('a', {}),
                        ('breast cancer treatment', {'entity_type': 'chemotherapy'})])
    parsed7 = specialist_lexicon.parse_words('I have a breast cancer treatments')
    assert (parsed7 == [('i', {}), ('have', {}), ('a', {}),
                        ('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'}),
                        ('treatments', {})])
    parsed8 = specialist_lexicon.parse_words('I had a breast cancer treatments and cancer test')
    assert (parsed8 == [('i', {}), ('had', {}), ('a', {}),
                        ('breast cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'}),
                        ('treatments', {}), ('and', {}),
                        ('cancer', {'snomed_tag': 'disorder', 'entity_type': 'disease', 'pipeline': 'cancer'}),
                        ('test', {})])
