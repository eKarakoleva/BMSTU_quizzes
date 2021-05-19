from re import S
from numpy.lib.function_base import append
import quizzes.models as model
import quizzes.repositories as repo
import quizzes.serializers as serializer
import numpy as np
from string import punctuation
my_punctuation = punctuation.replace("'", "").replace("_", "")

from quizzes.grammar.Tokenizer import Tokenizer, END_TOKEN
from quizzes.grammar.PoSTagger import PoSTagger
from quizzes.grammar.WordsConnect import WordsConnect

import quizzes.repositories as repo
import quizzes.models as model
from nltk.stem.snowball import SnowballStemmer
from quizzes.grammar.lang_abr import abr_to_lang

CORRECT_WORD = 1
WRONG_WORD = 2
NOT_FOUND_WORD = 3


SPELLING_MISTAKE = 0
WRONG_ORDER = 1
SPELLING_AND_ORDER = 2
TRANSLATION_MISTAKE = 3
NOT_IN_ETHALON = 4
GRAMMAR_MISTAKE = 5

def get_etalons(question_id):
    answerRepo = repo.AnswerRepository(model.Answers)
    ethalons = answerRepo.get_by_id_ordered(question_id)
    serdata =  serializer.AnswersSerializer(ethalons, many = True)
    return serdata.data


def get_all_words(sents, lang):
    posTagger = PoSTagger(lang = lang)
    tn = Tokenizer(lang = lang)
    wc = WordsConnect(lang = lang)
    words = dict()
    pos_sents = []
    bi_words = []
    tri_words = []
    for sent in sents:
        temp_pos_sents = []
        prepared_sent = tn.prepare_not_self_text(sent['name'])
        bi_words.append(tn.generate_ngrams([prepared_sent], 2)[0])
        tri_words.append(tn.generate_ngrams([prepared_sent], 3)[0])
        tags = posTagger.tag(sent['name'])
        for tag_info in tags:
            tag = tag_info.split(" ")
            _tag = tag[0].split()
            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                temp_pos_sents.append(_tag[1])
                token = tn.prepare_not_self_text(_tag[0])
                if token not in words.keys():
                    words[token] = []
                    words[token].append(_tag[1])
                else:
                    if _tag[1] not in words[token]:
                         words[token].append(_tag[1])
        pos_sents.append(temp_pos_sents)     
    
    bi_pos = dict()
    tri_pos = dict()
    bi_pos = tn.generate_different_ngrams(pos_sents, 2, bi_pos, end_tag = True)
    tri_pos = tn.generate_different_ngrams(pos_sents, 3, tri_pos, end_tag = True)
    #print("\nBI: ", words)


def ethalon_info_prepare(ethalons, lang, tn, posTagger):
    wc = WordsConnect(lang = lang)
    words = dict()
    pos_sents = []
    bi_words = []
    ethalon_sents = []
    nsubj_connections = dict()
    for ethalon in ethalons:
        temp_pos_sents = []
        nsubjcts = wc.words_nsubj(ethalon['name'])
        for nsubj in nsubjcts:
            nsubj_connections.update({nsubj[0]: nsubj[1]})
        #get all nsubj for ethalon
        #get nsubj for checked sedntence after deconstruction (construct with possible correct words). 
        # them compare by NN (none) and see if verb is the same one. If not => error in verb (if mistake is... )
        prepared_sent = tn.prepare_not_self_text(ethalon['name'])
        bi_words = merge_without_dub(bi_words, tn.generate_ngrams([prepared_sent], 2, end_tag = True)[0])
        #tri_words = merge_without_dub(tri_words, tn.generate_ngrams([prepared_sent], 3, end_tag = True)[0])
        tags = posTagger.tag(ethalon['name'])
        ethalon_sents.append(tn.word_by_sent([ethalon['name']])[0])
        for tag_info in tags:
            tag = tag_info.split(" ")
            _tag = tag[0].split()
            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                temp_pos_sents.append(_tag[1])
                token = tn.prepare_not_self_text(_tag[0])
                if token not in words.keys():
                    words[token] = _tag[2].lower()
        temp_pos_sents.append(END_TOKEN)
        pos_sents.append(temp_pos_sents)  

    bi_pos = dict()
    tri_pos = dict()
    print("CONNECTIONS: ", nsubj_connections)
    print("\nBI_POS_SENTS: ", pos_sents)
    bi_pos = tn.generate_different_ngrams(pos_sents, 2, bi_pos)
    words[END_TOKEN] = END_TOKEN
    #print("\nWORDS: ", words)
    #print("\nTRI_GRAMS_POS: ", bi_pos)

    #print("YESSS ", get_next_bi_gram_word(bi_words, 'every'))
    #print("\nTRI_GRAMS_WORDS: ", tri_words)
    print('\n\nETHALON_SENT ', ethalon_sents)
    return words, bi_words, bi_pos, ethalon_sents, nsubj_connections

def merge_without_dub(arr1, arr2):
    in_first = set(arr1)
    in_second = set(arr2)
    in_second_but_not_in_first = in_second - in_first

    return arr1 + list(in_second_but_not_in_first)

def get_next_bi_gram_word(bi_words, prev_word):
    words = []
    for word in bi_words:
        if prev_word in word:
            sp = word.split(' ')
            if sp[0] == prev_word:
                words.append(sp[1])
    return words

        
def prepare_checking_sents(sents, lang, tn, posTagger):
    sents = tn.tokenize_sent(sents)
    #print(sents)
    words_struct = dict()
    sent_counter = 0
    for sent in sents:
        word_counter = 0
        tags = posTagger.tag([sent])
        for tag_info in tags:
            tag = tag_info.split(" ")
            _tag = tag[0].split()
            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                token = tn.prepare_not_self_text(_tag[0])
                if sent_counter not in words_struct:
                    words_struct[sent_counter] = {}
                words_struct[sent_counter][word_counter] = {'word': token, 'new': '', 'error': [], 'pos': _tag[1]}

            word_counter += 1
        words_struct[sent_counter][word_counter] = {'word': END_TOKEN, 'new': '', 'error': [], 'pos': END_TOKEN}
        sent_counter += 1

    print("WORD_STRUCT_NEW: ", words_struct)
    return sents, words_struct

def process_checking(ethalons, checking_sents, lang):
    tn = Tokenizer(lang = lang)
    posTagger = PoSTagger(lang = lang)
    root_finder = SnowballStemmer(abr_to_lang(lang))
    words, bi_words, bi_pos, ethalon_sents, ethalon_nsubj_connections = ethalon_info_prepare(ethalons, lang, tn, posTagger)
    check_sent, words_struct = prepare_checking_sents(checking_sents, lang, tn, posTagger)
    process_mistakes(words, bi_words, bi_pos, ethalon_sents, check_sent, words_struct,ethalon_nsubj_connections, tn, posTagger, root_finder)

def get_word_pos(posTagger, sent):
    tags = posTagger.tag(sent)
    word_pos = dict()
    for tag in tags:
        tag_info = tag.split(" ")
        tag_info = tag_info[0].split()
        word = tag_info[0].lower()
        if word not in word_pos.keys():
            word_pos[word] = tag_info[1]
    return word_pos

def get_pos_tag(posTagger, word):
    tags = posTagger.tag(word)
    tag_info =tags[0].split(" ")
    tag_info = tag_info[0].split()
    return tag_info[1]

def process_mistakes(words_main_form_ethalon, bi_words_ethalon, bi_pos_ethalon, ethalon_sents, check_sent, words_struct, ethalon_nsubj_connections, tn, posTagger, root_finder):
    tags = posTagger.tag(check_sent)
    #print(tags)
    main_forms_checking_sent = dict()
    for tag in tags:
        tag_info = tag.split(" ")
        tag_info = tag_info[0].split()
        word = tag_info[0].lower()
        if word not in main_forms_checking_sent.keys():
            main_forms_checking_sent[word] = tag_info[2].lower()
    main_forms_checking_sent[END_TOKEN] = END_TOKEN
    #print("\nCHECK_POS: ", tags)
    print("\n\n\n\nWORDS: ", words_main_form_ethalon)
    print("\n\n\n\ROOTS: ", main_forms_checking_sent)
    print("word_struct: ", words_struct)
    #print("ETHALONS: ", ethalon_sents)
    bi_grams= tn.generate_ngrams(check_sent, 2, prepare = True, end_tag = True)
    print("\nBI_GRAMS: ", bi_words_ethalon)
    print("\nBI_POS: ", bi_pos_ethalon)
    #print(words_struct)
    sent_counter = 0
    print("STRUCT_before: ", words_struct)
    for sent_bigrams in bi_grams:    #check_sent
        bi_gram_counter = 0
        tokenized_sent = tn.tokenize_word(check_sent[sent_counter])
        tokenized_sent.append(END_TOKEN)
        for bi_gram in sent_bigrams: #check_sent
            bi_gramm_words = tn.word_by_sent([bi_gram])[0] #check_sent
            if len(bi_gramm_words) == 2:
                print("AAA: ", bi_gram, bi_gram_counter, bi_gram_counter + 1)
            #else:
            #   check for bi_grams
            if bi_gram not in bi_words_ethalon:  #ethalons
                for i in range(len(bi_gramm_words)):
                    if i == 0:
                        #print("CHECK: ", words_struct[bi_gramm_words[i]]['new'])
                        posible_words = []
                        possible_words_next = dict()
                        if bi_gramm_words[i] not in words_main_form_ethalon.keys():
                            if sent_counter in words_struct.keys():
                                if bi_gram_counter in words_struct[sent_counter].keys():
                                    if bi_gramm_words[i] in  words_struct[sent_counter][bi_gram_counter]['new']:
                                        next_word = list(words_struct[sent_counter][bi_gram_counter]['new'].keys())[0]
                                        possible_words_next = {next_word : -2} #alredy fixed word
                                    else:
                                        posible_words, possible_words_next = get_possible_correction_words(ethalon_sents, bi_gramm_words[i], "", words_main_form_ethalon, main_forms_checking_sent, root_finder)
                                        #print('WORD: ', bi_gramm_words[i])
                                        #print('POSIIBLE: ', posible_words, possible_words_next)
                                        if len(possible_words_next) == 0 and len(posible_words) == 0:
                                            possible_words_next = {bi_gramm_words[i] : -1} #NOT FOUND WORD
                        else: 
                            possible_words_next = {bi_gramm_words[i] : 0}       #NOT MISTAKEN WORD                       
                        
                        is_there_next_possinble_words = len(possible_words_next)
                        if i == 0:
                            #print("IIIIIIII ==== 0000")
                            if is_there_next_possinble_words != 0:
                                check_grammar_rules(i, sent_counter, bi_gram_counter, bi_gramm_words, possible_words_next, words_main_form_ethalon, bi_words_ethalon, bi_pos_ethalon, ethalon_sents, main_forms_checking_sent, words_struct, tokenized_sent, posTagger, root_finder)            
                            else:
                                check_grammar_rules(i, sent_counter, bi_gram_counter, bi_gramm_words, posible_words, words_main_form_ethalon, bi_words_ethalon, bi_pos_ethalon, ethalon_sents, main_forms_checking_sent, words_struct, tokenized_sent, posTagger, root_finder)  
            bi_gram_counter += 1 
        
        
        sent_counter += 1
        print("STRUCT: ", words_struct)

def check_grammar_rules(i, sent_count, bi_word_count, bi_gramm_words, posible_words, words_main_form_ethalon, bi_words_ethalon, bi_pos_ethalon, ethalon_sents, main_forms_checking_sent, words_struct, tokenized_sent, posTagger, root_finder):
    #print("\n+++ WRONG_WORD +++\n")
    next_word = bi_gramm_words[i + 1]
    #print("NEXT_WORD: ", next_word)
    #print("POSSIBLE_WORDS: ", posible_words)
    temp_error_struct = {'first_word': 'NONE', 'second_word': 'NONE', 'error_type': 'NONE'}
    word_is_correct = CORRECT_WORD
    if len(posible_words) != 0:
        #if not spelling, get word with higest posibility
        for pwn, prop in posible_words.items():
            tokenized_sent[bi_word_count] = pwn
            if prop != 0 and prop != -1:
                word_is_correct = WRONG_WORD
            if prop == -1:
                word_is_correct = NOT_FOUND_WORD
            if next_word in words_main_form_ethalon.keys():
                #print("NO MATCH0: ",pwn,  next_word)
                error_type = check_pos_grammar(i, sent_count, bi_word_count, pwn, next_word, bi_words_ethalon, bi_gramm_words,bi_pos_ethalon, words_struct, posTagger, tokenized_sent, temp_error_struct, word_correct = word_is_correct)
                #print("ERROR TYPE: ", error_type )
                if update_structs(error_type, pwn, next_word, words_struct, sent_count, bi_word_count, temp_error_struct):
                    break
            else:
                posible_words, possible_words_next = get_possible_correction_words(ethalon_sents, next_word, pwn, words_main_form_ethalon, main_forms_checking_sent, root_finder)
                if len(possible_words_next) != 0:
                    #print("NO MATCH1: ",pwn,  next_word, word_is_correct)
                    error_type = search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, possible_words_next, bi_words_ethalon,bi_pos_ethalon, words_struct, bi_gramm_words, tokenized_sent, temp_error_struct, word_is_correct, posTagger)
                else:
                   # print("NO MATCH2: ",pwn,  next_word, word_is_correct)
                    error_type = search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, posible_words, bi_words_ethalon,bi_pos_ethalon, words_struct, bi_gramm_words, tokenized_sent, temp_error_struct, word_is_correct, posTagger)
                if update_structs(error_type, pwn, next_word, words_struct, sent_count, bi_word_count, temp_error_struct):
                    break
                #print("ERROR TYPE2: ", error_type )
        if temp_error_struct['error_type'] != 'NONE':
            #print("\n IS VARY: ",  words_struct[sent_count][bi_word_count]['word'],  words_struct[sent_count][bi_word_count + 1]['word'], error_type)
            if temp_error_struct['error_type'] not in words_struct[sent_count][bi_word_count]['error']:
                words_struct[sent_count][bi_word_count]['error'].append(temp_error_struct['error_type'])
            tokenized_sent[bi_word_count] = temp_error_struct['first_word']
            if temp_error_struct['error_type'] not in words_struct[sent_count][bi_word_count + 1]['error']:
                words_struct[sent_count][bi_word_count + 1]['error'].append(temp_error_struct['error_type'])
            tokenized_sent[bi_word_count + 1] = temp_error_struct['second_word']
        print("\nTEMP_STRUCT: ", temp_error_struct)
        print("CHECK: ", tokenized_sent)


def search_for_second_word(i, sent_count, bi_word_count, first_word, second_word, possible_words, bi_words_ethalon,bi_pos_ethalon, words_struct, bi_gramm_words,tokenized_sent,temp_error_struct, word_is_correct, posTagger):
    is_in = 0
    error_type = SPELLING_MISTAKE
    #print("FIRST_SECOND: ", first_word, second_word)
    #print("POSSIBLE WORDS IN ", possible_words)
    for second_word in possible_words:
        tokenized_sent[bi_word_count + 1] = second_word
        next_next_word = first_word + " " + second_word
        #print("POSSIBLE WORDS first ", next_next_word)
        if next_next_word in bi_words_ethalon:
            is_in +=1
            print("\nSPELLING: ", next_next_word),
            update_words_struct(sent_count, bi_word_count, first_word, second_word, error_type, words_struct)
            return error_type
            #no more checking
        else:
            corrected_sent = " ".join(tokenized_sent)
            tag = get_word_pos(posTagger, corrected_sent)
            pos_bi_gramm = tag[first_word] + " " + tag[second_word]
            if pos_bi_gramm in bi_pos_ethalon:
                is_in +=1
                #words_struct[bi_gramm_words[i]]['new'] = {first_word: tag[first_word]}
                #words_struct[bi_gramm_words[i + 1]]['new'] = {second_word: tag[second_word]}
                print("\nWRONG_ORDER: ", pos_bi_gramm)
                return WRONG_ORDER
        if word_is_correct != NOT_FOUND_WORD:
            error_type = check_pos_grammar(i, sent_count, bi_word_count, first_word, second_word, bi_words_ethalon, bi_gramm_words,bi_pos_ethalon, words_struct, posTagger,tokenized_sent,temp_error_struct, word_correct = WRONG_WORD)
        else:
            error_type = check_pos_grammar(i, sent_count, bi_word_count, first_word, second_word, bi_words_ethalon, bi_gramm_words,bi_pos_ethalon, words_struct, posTagger,tokenized_sent,temp_error_struct, word_correct = NOT_FOUND_WORD)
    if len(possible_words) == 0:  #no possible words to change with
        #print("NO_CHANGEEE")
        error_type = check_pos_grammar(i, sent_count, bi_word_count, first_word, second_word, bi_words_ethalon, bi_gramm_words,bi_pos_ethalon, words_struct, posTagger,tokenized_sent,temp_error_struct, word_correct = NOT_FOUND_WORD)

    
    return error_type

def check_pos_grammar(i, sent_count, bi_word_count, first_word, second_word, bi_words_ethalon, bi_gramm_words,bi_pos_ethalon, words_struct, posTagger, tokenized_sent, temp_error_struct, word_correct):
    new_bi_gramm = first_word + " " + second_word
    error_type = SPELLING_MISTAKE
    if new_bi_gramm in bi_words_ethalon:
        if word_correct != CORRECT_WORD:
            print("\n + SPELLING: ", new_bi_gramm)
            error_type = SPELLING_MISTAKE
        else:
            print("\n NO_MISTAKE: ", new_bi_gramm)
    else:
        corrected_sent = " ".join(tokenized_sent)
        tag = get_word_pos(posTagger, corrected_sent)
        pos_bi_gramm = tag[first_word] + " " + tag[second_word]
        if second_word == END_TOKEN:
            pos_bi_gramm = tag[first_word] + " " + END_TOKEN
        #print("NEW_BI_GRAMM1: ", new_bi_gramm, pos_bi_gramm)
        if pos_bi_gramm in bi_pos_ethalon:
            #check out pos
            if word_correct == CORRECT_WORD:
                print("\nWRONG ORDER: ", new_bi_gramm)
                error_type = WRONG_ORDER
            if word_correct == WRONG_WORD:
                print("\nSPELLING + WRONG_ORDER1: ", new_bi_gramm)
                error_type = SPELLING_AND_ORDER
            if word_correct == NOT_FOUND_WORD:
                print("\nnTRANSLATION_WORD: ", new_bi_gramm)
                error_type = TRANSLATION_MISTAKE     
        else:

            tagsetRepo = repo.TagsetRepository(model.Tagset)
            tag1_id = tagsetRepo.get_tag_id(tag[first_word])
            tag2_id = tagsetRepo.get_tag_id(tag[second_word])
            if tag1_id != -1 and tag2_id != -1:
                bigramRepo = repo.BiGrammsRepository(model.BiGramms)
                is_grammarly_correct = bigramRepo.get_combination(tag1_id, tag2_id)
                #  print("\n\n\nIS_GRAMMARLY_CORRECT: ", is_grammarly_correct)
            #print("NEW_BI_GRAMM2: ", new_bi_gramm)
            ##CHECK IF WORD IS DIFFERENT FOR SPELLING MISTAKES
            #check out pos
            if word_correct == NOT_FOUND_WORD:
                if is_grammarly_correct != -1: #pos_out is okay:
                    print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) ", new_bi_gramm, pos_bi_gramm)
                    error_type = NOT_IN_ETHALON
                else:
                     print("\nWRONG GRAMMAR: ", new_bi_gramm)
                     error_type = GRAMMAR_MISTAKE
              
            else:
                if word_correct == CORRECT_WORD: #words are correct from the begginig:
                    if is_grammarly_correct != -1:
                        print("\nWRONG ORDER: ", new_bi_gramm, pos_bi_gramm)
                        error_type = WRONG_ORDER
                    else:
                        print("\nWRONG GRAMMAR: ", new_bi_gramm)
                        error_type = GRAMMAR_MISTAKE

                else:
                    if is_grammarly_correct != -1:
                        print("\nSPELLING + WRONG_ORDER2: ", new_bi_gramm, pos_bi_gramm)
                        error_type = SPELLING_AND_ORDER
                    else:
                        print("\nWRONG GRAMMAR: ", new_bi_gramm)
                        error_type = GRAMMAR_MISTAKE

        if error_type == SPELLING_AND_ORDER:
            update_words_struct(sent_count, bi_word_count, first_word, second_word, error_type, words_struct)
        else:
            update_temp_error_struct(first_word, second_word, error_type, temp_error_struct)

    return error_type

def get_possible_correction_words(sents, cur_word, next_word, words_main_form_ethalon, main_form_checking, root_finder):
    words = {}
    word_next = dict()
    for sent in sents:
        #if '__sent__' not in sent:
            #sent.append('__sent__')
        #print("\nSENT:\n: ", sent)
        sent_len = len(sent) - 1
        for index, ele in enumerate(sent):
            word_from_ethalon = ele.lower()
            if next_word != "":
                if word_from_ethalon == next_word and index != sent_len:
                    ethalon_word = sent[index+1]
                    if ethalon_word not in word_next:
                        if ethalon_word in words_main_form_ethalon.keys():
                            if words_main_form_ethalon[ethalon_word] != main_form_checking[cur_word]:
                                if root_finder.stem(cur_word) != root_finder.stem(ethalon_word):
                                    ratio = levenshtein_ratio_and_distance(ethalon_word, cur_word, ratio_calc = True)
                                    words_rates = words.values()
                                    if len(words) == 0:
                                        if ratio > 0.50:
                                            word_next.update({ethalon_word:ratio})
                                    else:
                                        if ratio > 0.50 and ratio >= max(words_rates):
                                            word_next.update({ethalon_word:ratio})
              
            if word_from_ethalon not in words and word_from_ethalon not in word_next and words_main_form_ethalon[word_from_ethalon] != main_form_checking[cur_word]:
                if root_finder.stem(cur_word) != root_finder.stem(word_from_ethalon):
                    ratio_all = levenshtein_ratio_and_distance(word_from_ethalon, cur_word, ratio_calc = True)
                    #print("EXCEPT: ", word_from_ethalon, cur_word,  ratio_all
                    words_rates = words.values()
                    if len(words_rates) != 0:
                        if ratio_all > 0.50 and ratio_all >= max(words_rates) and word_from_ethalon not in word_next: 
                            words.update({word_from_ethalon:ratio_all}) 
                    else: 
                        if ratio_all > 0.50:
                            words.update({word_from_ethalon:ratio_all}) 
                        #print("EXCEPT: ", word_from_ethalon, cur_word,  ratio_all)
    words = sort_dict(words)
    word_next = sort_dict(word_next)
    return words, word_next

def update_words_struct(sent_count, bi_word_count, first_word, second_word, error_type, words_struct):
    if words_struct[sent_count][bi_word_count]['word'] != first_word and not words_struct[sent_count][bi_word_count]['new']: 
        words_struct[sent_count][bi_word_count]['new'] = first_word
        if error_type not in words_struct[sent_count][bi_word_count]['error']:
            words_struct[sent_count][bi_word_count]['error'].append(error_type)
    if words_struct[sent_count][bi_word_count + 1]['word'] != second_word and not words_struct[sent_count][bi_word_count + 1]['new']: 
        words_struct[sent_count][bi_word_count + 1]['new'] = second_word
        if error_type not in words_struct[sent_count][bi_word_count + 1]['error']:
            words_struct[sent_count][bi_word_count + 1]['error'].append(error_type)

def update_temp_error_struct(first_word, second_word, error_type, temp_error_struct):
    if temp_error_struct['first_word'] == 'NONE':
        temp_error_struct['first_word'] = first_word
        temp_error_struct['second_word'] = second_word
        temp_error_struct['error_type'] = error_type

def update_structs(error_type, first_word, second_word, words_struct, sent_count, bi_word_count, temp_error_struct):
    to_break = 0
    if error_type == SPELLING_MISTAKE:
        update_words_struct(sent_count, bi_word_count, first_word, second_word, error_type, words_struct)
        to_break = 1
    else:
        update_temp_error_struct(first_word, second_word, error_type, temp_error_struct)
    return to_break
    
def sort_dict(dict_unsorted):
    if len(dict_unsorted) != 0:
        dict_unsorted = sorted(dict_unsorted.items(), key=lambda x: x[1], reverse=True)
        dict_unsorted= {k:v for k,v in dict_unsorted}
    return dict_unsorted

def best_ratio(next_words, cur_word, roots):
    ratio = 0
    best_word = ""
    for nw in next_words:
        temp_rat = levenshtein_ratio_and_distance(nw, cur_word, ratio_calc = True)
        if ratio < temp_rat:
            ratio = temp_rat
            best_word = nw
    return best_word, ratio

def best_ratio_all_words(words, cur_word):
    ratio = 0
    best_word = ""
    for word in words:
        temp_rat = levenshtein_ratio_and_distance(word, cur_word, ratio_calc = True)
        if ratio < temp_rat:
            ratio = temp_rat
            best_word = word
    return best_word, ratio

def levenshtein_ratio_and_distance(s, t, ratio_calc = False):
	rows = len(s)+1
	cols = len(t)+1
	distance = np.zeros((rows,cols),dtype = int)

	for i in range(1, rows):
		for k in range(1,cols):
			distance[i][0] = i
			distance[0][k] = k

	for col in range(1, cols):
		for row in range(1, rows):
			if s[row-1] == t[col-1]:
				cost = 0 
			else:
				if ratio_calc == True:
					cost = 2
				else:
					cost = 1
			distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
								 distance[row][col-1] + 1,          # Cost of insertions
								 distance[row-1][col-1] + cost)     # Cost of substitutions
	if ratio_calc == True:
		Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
		return Ratio
	else:
		return distance[row][col]

