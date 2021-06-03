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
import numpy as np


'''
WORD_WITH_NO_MISTAKE = 0
ALREADY_FIXED_WORD = -1
WORD_FORM_MISTAKE = -3
TRANSLATION_MISTAKE = -4
SPELLING_MISTAKE = -5
WRONG_ORDER = -6
SPELLING_AND_ORDER = -7
NOT_IN_ETHALON = -8
GRAMMAR_MISTAKE = -9
NOT_IN_ETHALON = -10
'''

SPELLING_MISTAKE = 0
WRONG_ORDER = -1
SPELLING_AND_ORDER = -2
TRANSLATION_MISTAKE = -3
NOT_IN_ETHALON = -4
GRAMMAR_MISTAKE = -5
WORD_FORM_MISTAKE = -6
WORD_WITH_NO_MISTAKE = -7
ALREADY_FIXED_WORD = -8


error_explain = {
    SPELLING_MISTAKE: "Spelling mistake",
    WRONG_ORDER: "Wrong order or need to be deleted",
    TRANSLATION_MISTAKE: "Translation mistake",
    NOT_IN_ETHALON: "Not in the ethalon",
    GRAMMAR_MISTAKE: "Grammar mistake",
    WORD_FORM_MISTAKE: "Word form mistake or wrong verb",
}

short_forms = {
    "'re": "are",
    "'m" : "am",
    "'s" : "is",
    "'ll": "will",
    "'ve": "have",
    "'d" : "would"
}

class GrammarChecker:
    def __init__(self, lang):
        self.lang = lang
        self.ethalon_sents = []
        self.checking_sents = []
        self.tokenizer = Tokenizer(lang = lang)
        self.posTagger = PoSTagger(lang = lang)
        self.rootFinder = SnowballStemmer(abr_to_lang(lang))
        self.wordConnector = WordsConnect(lang = lang)

        self.words_main_ethalon = dict()
        self.bi_words_ethalon = []
        self.bi_pos_ethalon = dict()
        self.nsubjs_ethalon = []
        self.auxs_ethalon = []
        self.pos_ethalon = dict()

        self.word_error_struct = dict()

    def ethalon_info_prepare(self, ethalons):
        pos_sents = []
        for ethalon in ethalons:
            temp_pos_sents = []
            text_withouth_sort_words = self.tokenizer.replace_short_forms(ethalon['name'].lower())
            self.nsubjs_ethalon, self.auxs_ethalon = self.wordConnector.words_nsubj_aux(text_withouth_sort_words)
            prepared_sent = self.tokenizer.prepare_not_self_text(ethalon['name'])
            self.bi_words_ethalon = self.merge_without_dub(self.bi_words_ethalon, self.tokenizer.generate_ngrams([prepared_sent], 2, end_tag = True)[0])
            tags = self.posTagger.tag(text_withouth_sort_words)
            
            self.ethalon_sents.append(self.tokenizer.word_by_sent([text_withouth_sort_words])[0])
            for tag_info in tags:
                tag = tag_info.split(" ")
                _tag = tag[0].split()
                if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                    temp_pos_sents.append(_tag[1])
                    token = self.tokenizer.prepare_not_self_text(_tag[0])
                    if token not in self.words_main_ethalon.keys():
                        self.words_main_ethalon[token] = _tag[2].lower()
                    if token not in self.pos_ethalon.keys():
                         self.pos_ethalon[token] = _tag[1]
            temp_pos_sents.append(END_TOKEN)
            temp_pos_sents.insert(0, END_TOKEN)
            pos_sents.append(temp_pos_sents)  

        self.bi_pos_ethalon = self.tokenizer.generate_different_ngrams(pos_sents, 2, self.bi_pos_ethalon)
        self.words_main_ethalon[END_TOKEN] = END_TOKEN


    def merge_without_dub(self, arr1, arr2):
        in_first = set(arr1)
        in_second = set(arr2)
        in_second_but_not_in_first = in_second - in_first

        return arr1 + list(in_second_but_not_in_first)

    def prepare_checking_sents(self, sents):
        self.checking_sents = self.tokenizer.tokenize_sent(sents)
        #print(sents)
        sent_counter = 0
        for sent in self.checking_sents:
            word_counter = 0
            tags = self.posTagger.tag([sent])
            for tag_info in tags:
                tag = tag_info.split(" ")
                _tag = tag[0].split()
                if _tag[1] != 'SENT':
                    token = self.tokenizer.prepare_not_self_text(_tag[0])
                    if sent_counter not in  self.word_error_struct:
                        self.word_error_struct[sent_counter] = {}
                    if word_counter == 0:
                        self.word_error_struct[sent_counter][word_counter] = {'word': END_TOKEN, 'new': '', 'error': []}
                        word_counter += 1
                    self.word_error_struct[sent_counter][word_counter] = {'word': token, 'new': '', 'error': []}


                word_counter += 1
            if sent_counter in  self.word_error_struct:
                 self.word_error_struct[sent_counter][word_counter] = {'word': END_TOKEN, 'new': '', 'error': []}
            sent_counter += 1

    def get_word_pos(self, sent):
        tags = self.posTagger.tag(sent)
        word_pos = dict()
        for tag in tags:
            tag_info = tag.split(" ")
            tag_info = tag_info[0].split()
            word = tag_info[0].lower()
            if word not in word_pos.keys():
                word_pos[word] = tag_info[1]
        return word_pos

    def get_words_pos_main_form(self, sent):
        tags = self.posTagger.tag(sent)
        word_pos = dict()
        main_form = dict()
        for tag in tags:
            tag_info = tag.split(" ")
            tag_info = tag_info[0].split()
            word = tag_info[0].lower()
            if word not in word_pos.keys():
                word_pos[word] = tag_info[1]
                main_form[word] = tag_info[2]
        return word_pos, main_form

    def get_words_pos_main_form(self, sent):
        tags = self.posTagger.tag(sent)
        word_pos = dict()
        main_form = dict()
        for tag in tags:
            tag_info = tag.split(" ")
            tag_info = tag_info[0].split()
            word = tag_info[0].lower()
            if word not in word_pos.keys():
                word_pos[word] = tag_info[1]
                main_form[word] = tag_info[2]
        return word_pos, main_form

    def process_mistakes(self):
        print("STRUCT: ", self.word_error_struct)
        tags = self.posTagger.tag(self.checking_sents)
        #print(tags)
        main_forms_checking_sent = dict()
        for tag in tags:
            tag_info = tag.split(" ")
            tag_info = tag_info[0].split()
            word = tag_info[0].lower()
            if word not in main_forms_checking_sent.keys():
                main_forms_checking_sent[word] = tag_info[2].lower()
        main_forms_checking_sent[END_TOKEN] = END_TOKEN
        bi_grams= self.tokenizer.generate_ngrams(self.checking_sents, 2, prepare = True, end_tag = True)
        
        tokenized_sent = []
        all_corected_sents = []
        sent_counter = 0
        for sent_bigrams in bi_grams:    #check_sent
            bi_gram_counter = 0
            tokenized_sent = self.tokenizer.tokenize_word(self.checking_sents[sent_counter])
            tokenized_sent.append(END_TOKEN)
            tokenized_sent.insert(0, END_TOKEN)
            for bi_gram in sent_bigrams: #check_sent
                bi_gramm_words = self.tokenizer.word_by_sent([bi_gram])[0] #check_sent

                if len(bi_gramm_words) == 2:
                    print("AAA: ", bi_gram, bi_gram_counter, bi_gram_counter + 1)
                #else:
                #   check for bi_grams
                if bi_gram not in self.bi_words_ethalon:  #ethalons
                    for i in range(len(bi_gramm_words)):
                        if i == 0:
                            posible_words = []
                            possible_words_next = dict()
                            if bi_gramm_words[i] not in self.words_main_ethalon.keys():
                                if sent_counter in self.word_error_struct.keys():
                                    if bi_gram_counter in self.word_error_struct[sent_counter].keys():
                                        #if bi_gramm_words[i] in  self.word_error_struct[sent_counter][bi_gram_counter]['word']:
                                        print("FIXED> ", self.word_error_struct[sent_counter][bi_gram_counter]['new'])
                                        if self.word_error_struct[sent_counter][bi_gram_counter]['new']:
                                            if WORD_FORM_MISTAKE in self.word_error_struct[sent_counter][bi_gram_counter]['error']:
                                                possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['new'] : WORD_FORM_MISTAKE} 
                                            else:   
                                               possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['new'] : SPELLING_MISTAKE} #alredy fixed word
                                        else:
                                            if TRANSLATION_MISTAKE in self.word_error_struct[sent_counter][bi_gram_counter]['error']:
                                                possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['word'] : TRANSLATION_MISTAKE} 
                                            else:
                                                posible_words, possible_words_next = self.get_possible_correction_words(bi_gramm_words[i], bi_gramm_words[i + 1], main_forms_checking_sent)
                                                if len(possible_words_next) == 0 and len(posible_words) == 0:
                                                    possible_words_next = {bi_gramm_words[i] : NOT_IN_ETHALON} #NOT FOUND WORD
                                                    #sent = " ".join(tokenized_sent)
                                                    sent = self.join_sent(tokenized_sent)
                                                    pos, main_forms = self.get_words_pos_main_form(sent)

                                                    if pos[bi_gramm_words[i]].startswith('V'):
                                                        possible_words_next = {key:WORD_FORM_MISTAKE for (key, value) in self.words_main_ethalon.items() if value == main_forms[bi_gramm_words[i]]}
                                                        if len(possible_words_next) == 0:
                                                            possible_words_next = {bi_gramm_words[i] : NOT_IN_ETHALON}
                                                    else:
                                                        print("AM I HERE")
                                                        for word, main_form_word in self.words_main_ethalon.items():
                                                            if main_form_word == main_forms[bi_gramm_words[i]]:
                                                                print("AM I HERE: ",main_form_word, main_forms[bi_gramm_words[i]] )
                                                                new_word = word
                                                                possible_words_next.update({new_word: WORD_FORM_MISTAKE})
                                                        if len(possible_words_next) == 0:
                                                            possible_words_next = {bi_gramm_words[i] : NOT_IN_ETHALON}

                            else: 
                                possible_words_next = {bi_gramm_words[i] : WORD_WITH_NO_MISTAKE}       #NOT MISTAKEN WORD                       
                            
                            is_there_next_possinble_words = len(possible_words_next)
                            if is_there_next_possinble_words != 0:
                                self.check_grammar_rules(i, sent_counter, bi_gram_counter, bi_gramm_words, possible_words_next, main_forms_checking_sent, tokenized_sent)           
                            else:
                                if len(posible_words) == 0:
                                    posible_words = {bi_gramm_words[i] : NOT_IN_ETHALON}
                                self.check_grammar_rules(i, sent_counter, bi_gram_counter, bi_gramm_words, posible_words, main_forms_checking_sent, tokenized_sent)
                bi_gram_counter += 1 
            
           
            tokenized_sent = self.fix_aux_connections(sent_counter, tokenized_sent, main_forms_checking_sent)
                                       
            sent_counter += 1
            all_corected_sents.append(tokenized_sent)
        print("STRUCT: ", self.word_error_struct)
        return all_corected_sents


    def fix_aux_connections(self, sent_counter, tokenized_sent, main_forms_checking_sent):
        tokenized_sent.remove(END_TOKEN)
        tokenized_sent.remove(END_TOKEN)
        
        corrected_sent = self.join_sent(tokenized_sent)
        print("\n\n\n\n\n\n\n\n\nCUR SENT: ", corrected_sent)
        _, auxs_connections_check = self.wordConnector.words_nsubj_aux_with_position(corrected_sent)
        print("AUXES: ", auxs_connections_check)
        print("AUXES2: ", self.auxs_ethalon)

        tokenized_sent.append(END_TOKEN)
        tokenized_sent.insert(0, END_TOKEN)
        print("TOKENIZED: ", tokenized_sent)
        
        if len(auxs_connections_check) != 0 and len(self.auxs_ethalon) == 0:
            for ncc in auxs_connections_check:
                print("DELETE: ", ncc)
                self.check_aux_if_not_expected(sent_counter, ncc, tokenized_sent, main_forms_checking_sent)
        for enc in self.auxs_ethalon:
            for ncc in auxs_connections_check:
                if enc[0] == ncc[0] and enc[1] != ncc[1]:
                    if enc[1] in short_forms.keys():
                        if short_forms[enc[1]] ==  ncc[1]:
                            break
                    else:
                        if ncc[1] in short_forms.keys():
                            if short_forms[ncc[1]] ==  ncc[1]:
                                break
                    
                    tags_1 = self.posTagger.tag(enc[1])
                    word1_tag = tags_1[0].split(" ")[0].split()
                
                    if not word1_tag[1].startswith("V") and word1_tag[1] != "MD":
                        tags_2 = self.posTagger.tag(ncc[1])
                        word2_tag = tags_2[0].split(" ")[0].split()
                        if not word2_tag[1].startswith("V") and word2_tag[1] != "MD":
                            break

                    print("ASASASA: ", ncc)
                    word_index = ncc[3]
                    self.remove_if_wrong_mistake(sent_counter, word_index)

                    self.word_error_struct[sent_counter][word_index]['error'].append(WORD_FORM_MISTAKE)
                    tokenized_sent[word_index] = enc[1]
                    self.word_error_struct[sent_counter][word_index]['new'] = enc[1]

                    new_analize_part = tokenized_sent[word_index - 1] + " " + tokenized_sent[word_index] + " " + tokenized_sent[word_index + 1]
                    bi_grams_re= self.tokenizer.generate_ngrams([new_analize_part], 2, prepare = False, end_tag = False)[0]
                    bi_gramm_words_re = self.tokenizer.word_by_sent(bi_grams_re)
                    word_index_re = word_index - 1

                    for bi_words_re in bi_gramm_words_re:
                        for j in range(len(bi_words_re)):
                            if j == 0:
                                if self.word_error_struct[sent_counter][word_index_re]['new']:
                                    if WORD_FORM_MISTAKE in self.word_error_struct[sent_counter][word_index_re]['error']:
                                        possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : WORD_FORM_MISTAKE} 
                                    else:   
                                        possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : SPELLING_MISTAKE}
                                else:
                                    if NOT_IN_ETHALON not in self.word_error_struct[sent_counter][word_index_re]['error'] and TRANSLATION_MISTAKE not in self.word_error_struct[sent_counter][word_index_re]['error']:
                                        possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : WORD_WITH_NO_MISTAKE} 
                                    else: 
                                        if NOT_IN_ETHALON in self.word_error_struct[sent_counter][word_index_re]['error']:
                                            possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : NOT_IN_ETHALON} 
                                        else:
                                            possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : TRANSLATION_MISTAKE} 
                                print("asas: ", word_index_re, bi_words_re, possible_words_next)
                                self.check_grammar_rules(j, sent_counter, word_index_re, bi_words_re, possible_words_next, main_forms_checking_sent, tokenized_sent)
                        word_index_re += 1
                else:
                    verb_exista_in_ethalon = any(ncc[0] in sublist for sublist in self.auxs_ethalon)
                    if not verb_exista_in_ethalon:
                        if ncc[1] in short_forms.keys():
                            if short_forms[ncc[1]] ==  ncc[1]:
                                break
                        self.check_aux_if_not_expected(sent_counter, ncc, tokenized_sent, main_forms_checking_sent)
                    
        return tokenized_sent 
        
    def remove_if_wrong_mistake(self, sent_counter, bi_word_count):
        errors = []
        for cur_error in self.word_error_struct[sent_counter][bi_word_count]['error']:
            if cur_error in self.word_error_struct[sent_counter][bi_word_count + 1]['error']:
                if bi_word_count + 2 in self.word_error_struct[sent_counter]:
                    if cur_error not in self.word_error_struct[sent_counter][bi_word_count + 2]['error']:
                        self.word_error_struct[sent_counter][bi_word_count + 1]['error'].remove(cur_error)
                else:
                    self.word_error_struct[sent_counter][bi_word_count + 1]['error'].remove(cur_error)
            if cur_error in self.word_error_struct[sent_counter][bi_word_count - 1]['error']:
                if bi_word_count - 2 in self.word_error_struct[sent_counter].keys():
                    if cur_error not in self.word_error_struct[sent_counter][bi_word_count - 2]['error']:
                        self.word_error_struct[sent_counter][bi_word_count - 1]['error'].remove(cur_error)
                else:
                    self.word_error_struct[sent_counter][bi_word_count - 1]['error'].remove(cur_error)

            if cur_error in self.word_error_struct[sent_counter][bi_word_count]['error']:
                errors.append(cur_error)
        for error in errors:
            self.word_error_struct[sent_counter][bi_word_count]['error'].remove(error)

    def check_aux_if_not_expected(self, sent_counter, ncc, tokenized_sent, main_forms_checking_sent):
        print("\n\n\n\n\DELETE: ", ncc)
        word_index = ncc[3]
        self.remove_if_wrong_mistake(sent_counter, word_index)

        self.word_error_struct[sent_counter][word_index]['error'].append(WORD_FORM_MISTAKE)
        self.append_if_not_exist(self.word_error_struct[sent_counter][word_index]['error'], NOT_IN_ETHALON)
        self.append_if_not_exist(self.word_error_struct[sent_counter][word_index + 1]['error'], NOT_IN_ETHALON)
        tokenized_sent[word_index] = ncc[1]
        self.word_error_struct[sent_counter][word_index]['new'] = ncc[1]

        new_analize_part = tokenized_sent[word_index - 1] + " " + tokenized_sent[word_index]
        bi_grams_re= self.tokenizer.generate_ngrams([new_analize_part], 2, prepare = False, end_tag = False)[0]
        bi_gramm_words_re = self.tokenizer.word_by_sent(bi_grams_re)
        word_index_re = word_index - 1

        for bi_words_re in bi_gramm_words_re:
            for j in range(len(bi_words_re)):
                if j == 0:
                    if self.word_error_struct[sent_counter][word_index_re]['new']:
                        if WORD_FORM_MISTAKE in self.word_error_struct[sent_counter][word_index_re]['error']:
                            possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : WORD_FORM_MISTAKE} 
                        else:   
                            possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : SPELLING_MISTAKE}
                    else:
                        if NOT_IN_ETHALON not in self.word_error_struct[sent_counter][word_index_re]['error'] and TRANSLATION_MISTAKE not in self.word_error_struct[sent_counter][word_index_re]['error']:
                            possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : WORD_WITH_NO_MISTAKE} 
                        else: 
                            if NOT_IN_ETHALON in self.word_error_struct[sent_counter][word_index_re]['error']:
                                possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : NOT_IN_ETHALON} 
                            else:
                                possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : TRANSLATION_MISTAKE} 
                    print("asas: ", word_index_re, bi_words_re, possible_words_next)
                    self.check_grammar_rules(j, sent_counter, word_index_re, bi_words_re, possible_words_next, main_forms_checking_sent, tokenized_sent)
            word_index_re += 1  

    def check_grammar_rules(self, i, sent_count, bi_word_count, bi_gramm_words, posible_words, main_forms_checking_sent, tokenized_sent):
        #print("\n+++ SPELLING_MISTAKE +++\n")
        next_word = bi_gramm_words[i + 1]
        print("NEXT_WORD: ", next_word)
        print("POSSIBLE_WORDS: ", posible_words)
        temp_error_struct = {'first_word': 'NONE', 'second_word': 'NONE', 'error_type': 'NONE'}
        word_is_correct = WORD_WITH_NO_MISTAKE

        if len(posible_words) != 0:
            #if not spelling, get word with higest posibility
            for pwn, prop in posible_words.items():
                tokenized_sent[bi_word_count] = pwn
                if prop != WORD_WITH_NO_MISTAKE and prop != NOT_IN_ETHALON:
                    if prop != WORD_FORM_MISTAKE:
                        if prop != TRANSLATION_MISTAKE:
                            word_is_correct = SPELLING_MISTAKE
                        else:
                             word_is_correct = TRANSLATION_MISTAKE
                    else:
                        word_is_correct = WORD_FORM_MISTAKE
                else:
                    word_is_correct = prop

                print("NO M: ", tokenized_sent)
                print("WORDS: ", pwn, word_is_correct)

                #if prop != WORD_FORM_MISTAKE and pwn not in short_forms.keys() and pwn not in short_forms.values():
                    #if self.compare_verb_roots(bi_gramm_words[i], pwn, tokenized_sent, bi_word_count):
                        #print("\n\n\nTAG_WORD: ", bi_gramm_words[i], pwn)
                        #tokenized_sent[bi_word_count] = bi_gramm_words[i]
                        #pwn = bi_gramm_words[i]
                        #word_is_correct = NOT_IN_ETHALON

                if word_is_correct == WORD_FORM_MISTAKE or word_is_correct == SPELLING_MISTAKE:
                    self.update_words_struct(sent_count, bi_word_count, pwn, self.word_error_struct[sent_count][bi_word_count + 1]['word'], word_is_correct)
                    word_is_correct = WORD_WITH_NO_MISTAKE

                print("WORDS2: ", next_word)
                if next_word in self.words_main_ethalon.keys():
                    print("NO MATCH0: ",pwn,  next_word, word_is_correct, tokenized_sent)
                    #word_is_correct - for first word
                    error_type = self.check_pos_grammar(pwn, next_word,tokenized_sent,temp_error_struct, word_is_correct)
                    print("ERROR TYPE: ", error_type )

                else:
                    #save_next = next_word 
                    print("SEARCH: ",pwn,  next_word, word_is_correct)              
                    posible_words, possible_words_next = self.get_possible_correction_words(next_word, pwn, main_forms_checking_sent)
                    if len(possible_words_next) != 0:
                        print("NO MATCH1: ",pwn,  next_word, word_is_correct, possible_words_next)
                        error_type, new_second_word = self.search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, possible_words_next, bi_gramm_words,tokenized_sent,temp_error_struct, word_is_correct)
                        next_word = new_second_word
                        print("WORDS: ",next_word )
                    else:
                        print("NO MATCH2: ",pwn,  next_word, word_is_correct, posible_words)
                        error_type, new_second_word = self.search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, posible_words, bi_gramm_words,tokenized_sent,temp_error_struct, word_is_correct)
                        next_word = new_second_word
                    print("ERROR TYPE2: ", error_type, next_word)
                    self.update_temp_error_struct(pwn, new_second_word, error_type, temp_error_struct)
                    

            print("\n\n\nAFTER_BREAK: ", temp_error_struct)       
            if temp_error_struct['error_type'] != 'NONE':
                error_t = temp_error_struct['error_type']
                if error_t == SPELLING_AND_ORDER or error_t == SPELLING_MISTAKE or error_t == WORD_FORM_MISTAKE:
                    self.update_words_struct(sent_count, bi_word_count, temp_error_struct['first_word'], temp_error_struct['second_word'], error_t)
                    print("\nWAWAWAWA: ", temp_error_struct['first_word'])
                    if temp_error_struct['first_word'] != END_TOKEN:
                        tokenized_sent[bi_word_count]  = temp_error_struct['first_word']
                    if temp_error_struct['second_word'] != END_TOKEN:
                        tokenized_sent[bi_word_count + 1] = temp_error_struct['second_word']
                else:
                    if error_t != WORD_WITH_NO_MISTAKE:
                        #if error_type != TRANSLATION_MISTAKE:
                        self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], error_t)
                        self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], error_t)
                       # else:
                            #self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], error_t)

            print("\nTEMP_STRUCT: ", temp_error_struct)
            print("CHECK: ", tokenized_sent)
            print("\nSTRUCT: ", self.word_error_struct)

    def search_for_second_word(self, i, sent_count, bi_word_count, first_word, second_word_, possible_words, bi_gramm_words,tokenized_sent,temp_error_struct, first_word_is_correct):
        skipped = 0
        error_type = SPELLING_MISTAKE
        word_correct = SPELLING_MISTAKE

        print("FIRST_SECOND: ", first_word, second_word_)
        print("POSSIBLE WORDS IN ", possible_words)
        for second_word in possible_words:
            second_word_ = second_word
            
            if possible_words[second_word] == WORD_FORM_MISTAKE:
                print("\nWORD FORM MISTAKE")
                self.update_words_struct(sent_count, bi_word_count, first_word,second_word, WORD_FORM_MISTAKE)
                tokenized_sent[bi_word_count + 1] = second_word
                word_correct =  WORD_FORM_MISTAKE
                #self.update_temp_error_struct(first_word, second_word, word_correct, temp_error_struct)
                #return WORD_FORM_MISTAKE, second_word  #form mistake?


            new_word_comb = first_word + " " + second_word
            if tokenized_sent[bi_word_count + 1] != END_TOKEN:
                tokenized_sent[bi_word_count + 1] = second_word


            #if self.compare_verb_roots(bi_gramm_words[i + 1], second_word, tokenized_sent, bi_word_count + 1) and word_correct !=  WORD_FORM_MISTAKE:
                #second_word = bi_gramm_words[i + 1]
                #tokenized_sent[bi_word_count + 1] = second_word
                #print("\n\n\nTAG_WORD2: ", first_word, second_word)
                #skipped = 1
                #continue
            
            print("NEW_comp2: ", new_word_comb)
            if new_word_comb in self.bi_words_ethalon: 
                print("\nSPELLING: ", new_word_comb),
                word_correct = SPELLING_MISTAKE
                self.update_temp_error_struct(first_word, second_word, word_correct, temp_error_struct)
            else:
                corrected_sent = self.join_sent(tokenized_sent)
                tag = self.get_word_pos(corrected_sent)
                pos_bi_gramm = tag[first_word] + " " + tag[second_word]
                print("ELSE: ", pos_bi_gramm, self.bi_pos_ethalon)
            
                if word_correct !=  WORD_FORM_MISTAKE:
                    if first_word_is_correct != NOT_IN_ETHALON:
                        print("\nSPELLING + WRONG_ORDER0: ", pos_bi_gramm, first_word, second_word)
                        word_correct = SPELLING_AND_ORDER
                    else:
                        print("\nNOT ETHALON1: ", pos_bi_gramm, first_word, second_word)
                        word_correct = NOT_IN_ETHALON 
                else:
                    
                    print("\nORDER: ", pos_bi_gramm, first_word, second_word, word_correct)
                    if first_word_is_correct != NOT_IN_ETHALON:
                        if first_word_is_correct == TRANSLATION_MISTAKE and pos_bi_gramm in self.bi_pos_ethalon:
                            word_correct = WORD_WITH_NO_MISTAKE
                        else:
                            word_correct = WRONG_ORDER   
                    else:
                        if pos_bi_gramm in self.bi_pos_ethalon:
                            word_correct = TRANSLATION_MISTAKE
                        else:
                            word_correct = NOT_IN_ETHALON                    

                self.update_temp_error_struct(first_word, second_word, word_correct, temp_error_struct)

            if possible_words[second_word] >= 0.81:
                break
                


            error_type = self.check_pos_grammar(first_word, second_word_, tokenized_sent, temp_error_struct, word_correct)

        if len(possible_words) == 0 or skipped:  #no possible words to change with
            print("NO_CHANGEEE", possible_words, second_word_)
            word_correct = NOT_IN_ETHALON
            save_word = second_word_
            if len(possible_words) == 0:
                if second_word_ in short_forms.keys():
                    if short_forms[second_word_] in self.words_main_ethalon.keys():
                        word_correct = WORD_WITH_NO_MISTAKE
                        second_word_ = short_forms[second_word_]
                        self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word_
                        tokenized_sent[bi_word_count+1] = second_word_
                else:
                    print("EXc: ",second_word_, short_forms.values())
                    if second_word_ in short_forms.values():
                        val_list = list(short_forms.values())
                        position = val_list.index(second_word_)
                        key_list = list(short_forms.keys())
                        second_word_ = key_list[position]
                        if second_word_ in self.words_main_ethalon.keys():
                            word_correct = WORD_WITH_NO_MISTAKE
                            print("EXcaaa: ",second_word_)
                            self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word_
                            tokenized_sent[bi_word_count+1] = second_word_
                        else:
                            second_word_ = save_word
                        del val_list
                        del key_list

                error_type = self.check_pos_grammar(first_word, second_word_,tokenized_sent,temp_error_struct, word_correct)
            else:
                error_type = self.check_pos_grammar(first_word, second_word_,tokenized_sent,temp_error_struct, word_correct = TRANSLATION_MISTAKE)
        return error_type, second_word_

    def check_pos_grammar(self, first_word, second_word, tokenized_sent, temp_error_struct, word_correct):
        new_bi_gramm = first_word + " " + second_word
        print("NEW_BI: ", new_bi_gramm, self.bi_words_ethalon)
        error_type = SPELLING_MISTAKE
        if new_bi_gramm in self.bi_words_ethalon:
            if word_correct == SPELLING_MISTAKE:
                print("\n + SPELLING: ", new_bi_gramm)
                error_type = SPELLING_MISTAKE
            else:
                print("\n NO_MISTAKE: ", new_bi_gramm)
                error_type = word_correct
        else:
            corrected_sent = self.join_sent(tokenized_sent)

            #print("corrected_sent: " , tokenized_sent)
            tag = self.get_word_pos(corrected_sent)
            print("\n SENT: ", tokenized_sent)
            print("\n TAG: ", tag)
            pos_bi_gramm = tag[first_word] + " " + tag[second_word]
            if second_word == END_TOKEN:
                pos_bi_gramm = tag[first_word] + " " + END_TOKEN
            else:
                if first_word == END_TOKEN:
                    pos_bi_gramm =  END_TOKEN + " " + tag[second_word]
            #print("NEW_BI_GRAMM1: ", new_bi_gramm, pos_bi_gramm)
            tagsetRepo = repo.TagsetRepository(model.Tagset)
            #print("GRAMMAR_CHECK: ", first_word, second_word, tag[first_word], tag[second_word])
            tag1_id = tagsetRepo.get_tag_id(tag[first_word])
            tag2_id = tagsetRepo.get_tag_id(tag[second_word])
            if tag1_id != -1 and tag2_id != -1:
                bigramRepo = repo.BiGrammsRepository(model.BiGramms)
                is_grammarly_correct = bigramRepo.get_combination(tag1_id, tag2_id)

                
            if pos_bi_gramm in self.bi_pos_ethalon:
                if is_grammarly_correct != 1:
                    print("ALL_Coo: ", first_word, second_word, pos_bi_gramm, word_correct)
                    if word_correct == WORD_WITH_NO_MISTAKE:
                        print("\nWRONG ORDER1: ", new_bi_gramm)
                        error_type = WRONG_ORDER
                    if word_correct == SPELLING_MISTAKE:
                        print("\nSPELLING + WRONG_ORDER1: ", new_bi_gramm)
                        error_type = SPELLING_AND_ORDER

                    if word_correct == NOT_IN_ETHALON or word_correct == TRANSLATION_MISTAKE:
                        print("\nnTRANSLATION_WORD: ", new_bi_gramm)
                        #get possible translation
                        error_type = TRANSLATION_MISTAKE     
                else:
                    print("\nWRONG GRAMMAR1: ", new_bi_gramm)
                    error_type = GRAMMAR_MISTAKE               
            else:
                print("ALL_Coo22: ", first_word, second_word, pos_bi_gramm, word_correct, self.bi_pos_ethalon)
                
                if word_correct == NOT_IN_ETHALON:
                    #if is_grammarly_correct != -1 or second_word == END_TOKEN:
                    print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) ", new_bi_gramm, pos_bi_gramm, is_grammarly_correct)
                    error_type = NOT_IN_ETHALON
                    #else:
                        #error_type = GRAMMAR_MISTAKE
                else:
                    if is_grammarly_correct != -1 or second_word == END_TOKEN:
                        if word_correct == WORD_WITH_NO_MISTAKE: #words are correct from the begginig:
                            print("\nWRONG ORDER2: ", new_bi_gramm, pos_bi_gramm)
                            error_type = WRONG_ORDER
                        else:
                            if word_correct != WORD_FORM_MISTAKE :
                                print("\nSPELLING + WRONG_ORDER2: ", new_bi_gramm, pos_bi_gramm)
                                error_type = SPELLING_AND_ORDER
                            else:
                                print("\n WRONG_ORDER3: ", new_bi_gramm, pos_bi_gramm)
                                error_type = WRONG_ORDER
                    else:
                        print("\nWRONG GRAMMAR2: ", new_bi_gramm)
                        error_type = GRAMMAR_MISTAKE

            self.update_temp_error_struct(first_word, second_word, error_type, temp_error_struct)
        return error_type
        
    def get_possible_correction_words(self, cur_word, next_word, main_form_checking):
        words = {}
        word_next = dict()
        for sent in self.ethalon_sents:
            sent_len = len(sent) - 1
            for index, ele in enumerate(sent):
                word_from_ethalon = ele.lower()
                if next_word != "":
                    if word_from_ethalon == next_word and index != sent_len:
                        ethalon_word = sent[index+1]
                        if ethalon_word not in word_next:
                            if ethalon_word in self.words_main_ethalon.keys():
                                #print("HERERERE: ", ethalon_word, cur_word)
                                #print(self.words_main_ethalon)
                                #print("HERERERE1: ", self.words_main_ethalon[ethalon_word], main_form_checking[cur_word])
                                if ethalon_word in self.words_main_ethalon.keys() and cur_word in main_form_checking.keys():
                                    if self.words_main_ethalon[ethalon_word] != main_form_checking[cur_word]:
                                        self.word_possible_root_precess(ethalon_word, cur_word, word_next, words)
                                        #print("WHATATATA: ", word_next)
                                    else:
                                        ratio = self.levenshtein_ratio_and_distance(ethalon_word, cur_word, ratio_calc = True)
                                        #print("SAME FORMS???: ", self.words_main_ethalon[ethalon_word], main_form_checking[cur_word])
                                        if ethalon_word in short_forms.keys() or ethalon_word in short_forms.values() and ratio > 0.3:
                                            word_next.update({ethalon_word: WORD_WITH_NO_MISTAKE})
                                        else:
                                            word_next.update({ethalon_word: WORD_FORM_MISTAKE})
                            
                if word_from_ethalon not in words and word_from_ethalon not in word_next:  
                    if word_from_ethalon in self.words_main_ethalon.keys():
                        #print("HERERERE222: ", word_from_ethalon, cur_word)
                        #print("HERERERE221: ", self.words_main_ethalon[word_from_ethalon], main_form_checking[cur_word])
                        if word_from_ethalon in self.words_main_ethalon.keys() and cur_word in main_form_checking.keys():
                            if self.words_main_ethalon[word_from_ethalon] != main_form_checking[cur_word]:
                                #print("WHATATATA12: ", words)
                                self.word_possible_root_precess(word_from_ethalon, cur_word, words, word_next)
                                #print("WHATATATA22: ", words)
                            else:
                                #print("SAME FORMS22???: ", self.words_main_ethalon[word_from_ethalon], main_form_checking[cur_word])
                                ratio = self.levenshtein_ratio_and_distance(word_from_ethalon, cur_word, ratio_calc = True)
                                if word_from_ethalon in short_forms.keys() or word_from_ethalon in short_forms.values() and ratio > 0.3:
                                    words.update({word_from_ethalon: WORD_WITH_NO_MISTAKE})
                                else:
                                    words.update({word_from_ethalon: WORD_FORM_MISTAKE})  
                   


        words = self.sort_dict(words)
        word_next = self.sort_dict(word_next)
        return words, word_next

    def word_possible_root_precess(self, ethalon_word, cur_word, word_next_arr, words_arr):
        ratio = self.levenshtein_ratio_and_distance(ethalon_word, cur_word, ratio_calc = True)
        #print("RATIO: ", ratio)
        if ratio < 0.75:
            root_cur =  self.rootFinder.stem(cur_word)
            root_eth =  self.rootFinder.stem(ethalon_word)
            #if root_eth in root_cur:
                #word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
            if len(root_cur) > len(root_eth):
                new_root = root_cur[:len(root_cur) - (len(root_cur) - len(root_eth))]
                if len(new_root) >= 3:
                    root_cur = new_root
            ratio_root = self.levenshtein_ratio_and_distance(root_cur, root_eth, ratio_calc = True)
            #print("HERERERE_RATIO: ", ratio_root, root_cur, root_eth, ratio)
            if ratio_root >= 0.75:
                word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
            else:
                if ratio_root >= 0.5 and len(cur_word) <= 3: #for short words like do, ate ...
                    #print("\n\nELSE2.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                    if self.pos_ethalon[ethalon_word].startswith("V"):
                        #print("\n\nELSE3: ", self.pos_ethalon[ethalon_word])
                        tags = self.posTagger.tag(cur_word)
                        for tag_info in tags:
                            tag = tag_info.split(" ")
                            _tag = tag[0].split()
                            #print("\n\nELSE4: ", _tag)
                            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                 if _tag[1].startswith("V") or _tag[1] == 'MD':
                                    word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})

                                    
        if ratio >= 0.75:
            root1 = self.rootFinder.stem(cur_word)
            root2 = self.rootFinder.stem(ethalon_word)
            if root1 != root2:
                words_rates = words_arr.values()
                if len(words_arr) == 0:
                    max_rate = 0
                else:
                    max_rate = max(words_rates)

                if ratio > 0.65 and ratio >= max_rate:
                    word_next_arr.update({ethalon_word:ratio})
                    print("IAGAGAGAGAGAGAGAG", word_next_arr)
                print("HERERERE_RATIO_ИН_ИН: ", cur_word, ethalon_word, ratio, max_rate)
            else:
               print("WHY HERE: ", root1, root2)
               word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE}) 

            print("\n\nELSE1: ", ethalon_word, cur_word, self.pos_ethalon.keys())
            if ethalon_word in self.pos_ethalon.keys():
                keep_going = 1
                if ethalon_word in word_next_arr:
                    if word_next_arr[ethalon_word] >= 0.8:
                        keep_going = 0
                    if keep_going:     
                        print("\n\nELSE1.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                        if self.pos_ethalon[ethalon_word].startswith("V"):
                            print("\n\nELSE2: ", self.pos_ethalon[ethalon_word])
                            tags = self.posTagger.tag(cur_word)
                            for tag_info in tags:
                                tag = tag_info.split(" ")
                                _tag = tag[0].split()
                                print("\n\nELSE3: ", _tag)
                                if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                    if _tag[1].startswith("V") or _tag[1] == 'MD':
                                        word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
        print("MID RES: ", word_next_arr)

    def check_for_verbs(self, ethalon_word, cur_word, word_next_arr):
        print("\n\nELSE1: ", ethalon_word, cur_word, self.pos_ethalon.keys())
        if ethalon_word in self.pos_ethalon.keys():
            keep_going = 1
            if ethalon_word in word_next_arr:
                if word_next_arr[ethalon_word] >= 0.8:
                    keep_going = 0
                if keep_going:     
                    print("\n\nELSE1.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                    if self.pos_ethalon[ethalon_word].startswith("V"):
                        print("\n\nELSE2: ", self.pos_ethalon[ethalon_word])
                        tags = self.posTagger.tag(cur_word)
                        for tag_info in tags:
                            tag = tag_info.split(" ")
                            _tag = tag[0].split()
                            print("\n\nELSE3: ", _tag)
                            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                if _tag[1].startswith("V") or _tag[1] == 'MD':
                                    word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
    def update_words_struct(self, sent_count, bi_word_count, first_word, second_word, error_type):
        errors = error_type
        if error_type == SPELLING_AND_ORDER:
            errors = SPELLING_MISTAKE
            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], WRONG_ORDER)
            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], WRONG_ORDER)

        print("CHECK1_CHECK1: ", self.word_error_struct[sent_count][bi_word_count]['word'], first_word, error_type )
        if self.word_error_struct[sent_count][bi_word_count]['word'] != first_word and not self.word_error_struct[sent_count][bi_word_count]['new'] and first_word != END_TOKEN: 
            self.word_error_struct[sent_count][bi_word_count]['new'] = first_word
            if error_type not in self.word_error_struct[sent_count][bi_word_count]['error']:
                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], errors)
        
        print("CHECK2_CHECK2: ", self.word_error_struct[sent_count][bi_word_count + 1]['word'], second_word)
        if self.word_error_struct[sent_count][bi_word_count + 1]['word'] != second_word and not self.word_error_struct[sent_count][bi_word_count + 1]['new'] and second_word != END_TOKEN: 
            self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word
            if error_type not in self.word_error_struct[sent_count][bi_word_count + 1]['error']:
                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], errors)
        print("STRUCT_TEMP: ", self.word_error_struct)


    def update_temp_error_struct(self, first_word, second_word, error_type, temp_error_struct):
        print("TEMP_struct_IN: ", temp_error_struct)
        if temp_error_struct['first_word'] == 'NONE' or error_type == WORD_FORM_MISTAKE:
            temp_error_struct['first_word'] = first_word
            temp_error_struct['second_word'] = second_word
            temp_error_struct['error_type'] = error_type
       
        print("TEMP_struct_OUT: ", temp_error_struct)

    def update_structs(self,error_type, first_word, second_word, sent_count, bi_word_count, temp_error_struct):
        to_break = 0
        if error_type == SPELLING_MISTAKE or error_type == WORD_FORM_MISTAKE:
            self.update_words_struct(sent_count, bi_word_count, first_word, second_word, error_type)
            to_break = 1
        else:
            self.update_temp_error_struct(first_word, second_word, error_type, temp_error_struct)
        #print("UPDATE_STRUCT_MAIN_STAUS: ", to_break)
        return to_break


    def compare_verb_roots(self, original_word, new_word, tokenized_sent, bi_word_count):
        corrected_sent = self.join_sent(tokenized_sent)
        tag = self.get_word_pos(corrected_sent)
        ret_val = 0
        #print("\n\n\n\nKARA: ", new_word, tag[new_word])
        if tag[new_word].startswith('V'):
            ratio = self.levenshtein_ratio_and_distance(new_word, original_word, ratio_calc = True)
            #print("KARARA_RATIO: ", ratio)
            if ratio < 0.85:
                #print("\n\n\n\nKARATATATA: ", original_word, new_word)
                if original_word != new_word:
                    root1 = self.rootFinder.stem(original_word) 
                    root2 = self.rootFinder.stem(new_word) 
                    if len(root1) > len(root2):
                        root1 = root1[:len(root1) + 1 - (len(root1) - len(root2))]
                    #print("\nGGGG: ", root1, root2)
                    ratio_roots = self.levenshtein_ratio_and_distance(root1, root2, ratio_calc = True)
                    #print("\nRATIO: ", ratio_roots)
                    if ratio_roots <= 0.60: #Have same root?
                        #print("\n\nRATIO_IN: ", ratio_roots) #no they havent
                        new_word = original_word
                        corrected_sent = self.join_sent(tokenized_sent)
                        ret_val = 1 

        return ret_val

    def append_if_not_exist(self, array, val):
        if val not in array:
            array.append(val)

    def sort_dict(self, dict_unsorted):
        if len(dict_unsorted) != 0:
            dict_unsorted = sorted(dict_unsorted.items(), key=lambda x: x[1], reverse=True)
            dict_unsorted= {k:v for k,v in dict_unsorted}
        return dict_unsorted

    def levenshtein_ratio_and_distance(self, s, t, ratio_calc = False):
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

    def process_checking(self, ethalons, checking_sents):
        self.ethalon_info_prepare(ethalons)
        self.prepare_checking_sents(checking_sents)
        corrected_sent= self.process_mistakes()
        corrected_sent = self.remove_end_tags_corrected_sents(corrected_sent)
        return self.word_error_struct, error_explain, corrected_sent

    def remove_end_tags_corrected_sents(self, sents):
        corr_sents = ""
        for sent in sents:
            print(sent)
            while END_TOKEN in sent:
                sent.remove(END_TOKEN)
            sent = self.join_sent(sent)
            if len(sents) > 1:
                sent += " /"
            corr_sents += sent + " "
        return corr_sents
    
    def join_sent(self, arr_sent):
        sent = ""
        for word in arr_sent:
            if word.startswith("'"):
                sent += word
            else:
                sent += " " + word
        return sent
           
    def reset(self):
        self.ethalon_sents = []
        self.checking_sents = []
        self.words_main_ethalon = dict()
        self.bi_words_ethalon = []
        self.bi_pos_ethalon = dict()
        self.nsubjs_ethalon = []
        self.auxs_ethalon = []
        self.word_error_struct = dict()


def get_etalons(question_id):
    answerRepo = repo.AnswerRepository(model.Answers)
    ethalons = answerRepo.get_by_id_ordered(question_id)
    serdata =  serializer.AnswersSerializer(ethalons, many = True)
    return serdata.data

def process_checking(ethalons, checking_sents, lang):
    gc = GrammarChecker(lang)
    _, error_explain, corrected_sent = gc.process_checking(ethalons, checking_sents)
    return gc.word_error_struct, error_explain, corrected_sent




