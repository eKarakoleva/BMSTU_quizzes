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

'''
error_explain = {
    SPELLING_MISTAKE: "Spelling mistake",
    WRONG_ORDER: "Wrong order or need to be deleted",
    TRANSLATION_MISTAKE: "Translation mistake",
    NOT_IN_ETHALON: "Not in the ethalon",
    GRAMMAR_MISTAKE: "Grammar mistake",
    WORD_FORM_MISTAKE: "Word form mistake or wrong verb",
}
'''
error_explain = {
    SPELLING_MISTAKE: "Орфографическая ошибка",
    WRONG_ORDER: "Неправильный порядок слов или нужно удаление",
    TRANSLATION_MISTAKE: "Ошибка в переводе",
    NOT_IN_ETHALON: "Конструкция или слово не присуствует в эталоне",
    GRAMMAR_MISTAKE: "Грамматическая ошибка",
    WORD_FORM_MISTAKE: "Ошибка в форме слова или неправилыный глагол",
}

short_forms = {
    "'re": "are",
    "'m" : "am",
    "'s" : "is",
    "'ll": "will",
    "'ve": "have",
    "'d" : "would",
    "i"  : "I"
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

    def ethalon_info_prepare(self, ethalons, test = False):
        pos_sents = []
        for ethalon in ethalons:
            if not test:
                ethalon = ethalon['name']
            temp_pos_sents = []
            text_withouth_sort_words = self.tokenizer.replace_short_forms(ethalon.lower())
            self.nsubjs_ethalon, self.auxs_ethalon = self.wordConnector.words_nsubj_aux(text_withouth_sort_words)
            prepared_sent = self.tokenizer.prepare_not_self_text(ethalon)
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
        sents = self.tokenizer.make_downcase(sents)
        self.checking_sents = self.tokenizer.tokenize_sent(sents)
        ##print(sents)
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
        if END_TOKEN not in word_pos.keys():
            word_pos[END_TOKEN] = END_TOKEN
        return word_pos

    def get_words_pos_main_form(self, sent):
        #sent = self.tokenizer.prepare_not_self_text(sent)
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
        #print("STRUCT: ", self.word_error_struct)
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

                #if len(bi_gramm_words) == 2:
                    ##print("AAA: ", bi_gram, bi_gram_counter, bi_gram_counter + 1)
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
                                        #print("FIXED> ", self.word_error_struct[sent_counter][bi_gram_counter]['new'])
                                        if self.word_error_struct[sent_counter][bi_gram_counter]['new']:
                                            #print("FIXED>1 ")
                                            if WORD_FORM_MISTAKE in self.word_error_struct[sent_counter][bi_gram_counter]['error']:
                                                possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['new'] : WORD_FORM_MISTAKE} 
                                            else:   
                                               #possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['new'] : SPELLING_MISTAKE} #alredy fixed word
                                               posible_words, possible_words_next = self.get_possible_correction_words(bi_gramm_words[i], bi_gramm_words[i + 1], main_forms_checking_sent)
                                        else:
                                            #print("FIXED>2 ")
                                            not_word_form_mistake = 1
                                            if WORD_FORM_MISTAKE in self.word_error_struct[sent_counter][bi_gram_counter]['error']:
                                                if not self.word_error_struct[sent_counter][bi_gram_counter]['new']:
                                                    possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['word'] : WORD_FORM_MISTAKE} 
                                                    not_word_form_mistake = 0
    
                                            if not_word_form_mistake:
                                                #print("FIXED>3 ")
                                                if TRANSLATION_MISTAKE in self.word_error_struct[sent_counter][bi_gram_counter]['error']:
                                                    possible_words_next = {self.word_error_struct[sent_counter][bi_gram_counter]['word'] : TRANSLATION_MISTAKE} 
                                                else:
                                                    posible_words, possible_words_next = self.get_possible_correction_words(bi_gramm_words[i], bi_gramm_words[i + 1], main_forms_checking_sent)
                                                    if len(possible_words_next) == 0 and len(posible_words) == 0:
                                                        possible_words_next = {bi_gramm_words[i] : NOT_IN_ETHALON} #NOT FOUND WORD
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
            tokenized_sent = []
        #print("STRUCT: ", self.word_error_struct)
        self.remove_if_alone_status_code()
        print("STRUCT: ", self.word_error_struct)
        return all_corected_sents


    def fix_aux_connections(self, sent_counter, tokenized_sent, main_forms_checking_sent):
        tokenized_sent.remove(END_TOKEN)
        tokenized_sent.remove(END_TOKEN)
        
        corrected_sent = self.join_sent(tokenized_sent)
        #print("\n\n\n\n\n\n\n\n\nCUR SENT: ", corrected_sent)
        _, auxs_connections_check = self.wordConnector.words_nsubj_aux_with_position(corrected_sent)
        #print("AUXES_check: ", auxs_connections_check)
        #print("AUXES_ethalon: ", self.auxs_ethalon)

        tokenized_sent.append(END_TOKEN)
        tokenized_sent.insert(0, END_TOKEN)
        #print("TOKENIZED: ", tokenized_sent)
        
        if len(auxs_connections_check) != 0 and len(self.auxs_ethalon) == 0:
            for ncc in auxs_connections_check:
                #print("DELETE: ", ncc)
                self.check_aux_if_not_expected(sent_counter, ncc, tokenized_sent, main_forms_checking_sent)
        for enc in self.auxs_ethalon:
            for ncc in auxs_connections_check:
                if enc[0] == ncc[0] and enc[1] != ncc[1]:
                    verb_count = sum(x.count(ncc[0]) for x in auxs_connections_check)
                    if verb_count > 1:
                        possition_count = sum(x.count(ncc[2]) for x in auxs_connections_check)
                        if possition_count > 1:
                            break
                    if enc[1] in short_forms.keys():
                        if short_forms[enc[1]] ==  ncc[1]:
                            break
                    else:
                        if ncc[1] in short_forms.keys():
                            if short_forms[ncc[1]] ==  ncc[1]:
                                break
                    
                    tags_1 = self.posTagger.tag(enc[1])
                    word1_tag = tags_1[0].split(" ")[0].split()
                    tags_2 = self.posTagger.tag(ncc[1])
                    word2_tag = tags_2[0].split(" ")[0].split()

                    if not word1_tag[1].startswith("V") and word1_tag[1] != "MD" or not word2_tag[1].startswith("V") and word2_tag[1] != "MD":
                        break    

                    #print("ASASASA: ", ncc)
                    word_index = ncc[3]
                    self.remove_if_wrong_mistake(sent_counter, word_index)

                    self.append_if_not_exist(self.word_error_struct[sent_counter][word_index]['error'], WORD_FORM_MISTAKE)
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
                                        #print()
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
                                #print("asas: ", word_index_re, bi_words_re, possible_words_next)
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
            if cur_error != WORD_FORM_MISTAKE and cur_error != GRAMMAR_MISTAKE:
                if cur_error in self.word_error_struct[sent_counter][bi_word_count + 1]['error']:
                    if bi_word_count + 2 in self.word_error_struct[sent_counter]:
                        if cur_error not in self.word_error_struct[sent_counter][bi_word_count + 2]['error']:
                            self.word_error_struct[sent_counter][bi_word_count + 1]['error'].remove(cur_error)
                    else:
                        self.word_error_struct[sent_counter][bi_word_count + 1]['error'].remove(cur_error)
            if cur_error in self.word_error_struct[sent_counter][bi_word_count - 1]['error']:
                if cur_error != WORD_FORM_MISTAKE and cur_error != GRAMMAR_MISTAKE:
                    if bi_word_count - 2 in self.word_error_struct[sent_counter].keys():
                        if cur_error not in self.word_error_struct[sent_counter][bi_word_count - 2]['error']:
                            self.word_error_struct[sent_counter][bi_word_count - 1]['error'].remove(cur_error)
                    else:
                        self.word_error_struct[sent_counter][bi_word_count - 1]['error'].remove(cur_error)

            if cur_error in self.word_error_struct[sent_counter][bi_word_count]['error'] and cur_error != WORD_FORM_MISTAKE and cur_error != GRAMMAR_MISTAKE:
                errors.append(cur_error)
        for error in errors:
            self.word_error_struct[sent_counter][bi_word_count]['error'].remove(error)

    def check_aux_if_not_expected(self, sent_counter, ncc, tokenized_sent, main_forms_checking_sent):
        #print("\n\n\n\n\DELETE: ", ncc)

        tags_1 = self.posTagger.tag(ncc[1])
        word1_tag = tags_1[0].split(" ")[0].split()
        #print("TAG: ", word1_tag[1])
        if word1_tag[1].startswith("V") or word1_tag[1] == "MD":
       
            word_index = ncc[3]
            #self.remove_if_wrong_mistake(sent_counter, word_index)

            #self.word_error_struct[sent_counter][word_index]['error'].append(WORD_FORM_MISTAKE)
            if self.word_error_struct[sent_counter][word_index]['word'] != ncc[1]:
                self.append_if_not_exist(self.word_error_struct[sent_counter][word_index]['error'], WORD_FORM_MISTAKE)
            #self.append_if_not_exist(self.word_error_struct[sent_counter][word_index]['error'], NOT_IN_ETHALON)
            #self.append_if_not_exist(self.word_error_struct[sent_counter][word_index + 1]['error'], NOT_IN_ETHALON)
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
                                #print()
                                possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : WORD_FORM_MISTAKE} 
                            else:   
                                possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['new'] : SPELLING_MISTAKE}
                        else:
                            if NOT_IN_ETHALON not in self.word_error_struct[sent_counter][word_index_re]['error'] and TRANSLATION_MISTAKE not in self.word_error_struct[sent_counter][word_index_re]['error']:
                                possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : WORD_FORM_MISTAKE} 
                            else: 
                                if NOT_IN_ETHALON in self.word_error_struct[sent_counter][word_index_re]['error']:
                                    possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : NOT_IN_ETHALON} 
                                else:
                                    possible_words_next = {self.word_error_struct[sent_counter][word_index_re]['word'] : TRANSLATION_MISTAKE} 
                        #print("asas: ", word_index_re, bi_words_re, possible_words_next)
                        self.check_grammar_rules(j, sent_counter, word_index_re, bi_words_re, possible_words_next, main_forms_checking_sent, tokenized_sent)
                word_index_re += 1  

    def remove_if_alone_status_code(self):
        for sent_count in self.word_error_struct.keys():
            for word_count in range(1, len(self.word_error_struct[sent_count]) - 1):
                for code in self.word_error_struct[sent_count][word_count]['error']:
                    if code != SPELLING_MISTAKE and code != WORD_FORM_MISTAKE:
                        if code not in self.word_error_struct[sent_count][word_count - 1]['error'] and code not in self.word_error_struct[sent_count][word_count + 1]['error']:
                            self.word_error_struct[sent_count][word_count]['error'].remove(code)


    def check_grammar_rules(self, i, sent_count, bi_word_count, bi_gramm_words, posible_words, main_forms_checking_sent, tokenized_sent):
        ##print("\n+++ SPELLING_MISTAKE +++\n")
        next_word = bi_gramm_words[i + 1]
        #print("NEXT_WORD: ", next_word)
        #print("POSSIBLE_WORDS: ", posible_words)
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

                #print("NO M: ", tokenized_sent)
                #print("WORDS: ", pwn, word_is_correct)

                #if prop != WORD_FORM_MISTAKE and pwn not in short_forms.keys() and pwn not in short_forms.values():
                    #if self.compare_verb_roots(bi_gramm_words[i], pwn, tokenized_sent, bi_word_count):
                        #print("\n\n\nTAG_WORD: ", bi_gramm_words[i], pwn)
                        #tokenized_sent[bi_word_count] = bi_gramm_words[i]
                        #pwn = bi_gramm_words[i]
                        #word_is_correct = NOT_IN_ETHALON

                if word_is_correct == WORD_FORM_MISTAKE or word_is_correct == SPELLING_MISTAKE:
                    self.update_words_struct(sent_count, bi_word_count, pwn, self.word_error_struct[sent_count][bi_word_count + 1]['word'], word_is_correct)
                    if word_is_correct != WORD_FORM_MISTAKE:
                        word_is_correct = WORD_WITH_NO_MISTAKE

                #print("WORDS2: ", next_word)
                if next_word in self.words_main_ethalon.keys():
                    #print("NO MATCH0: ",pwn,  next_word, word_is_correct, tokenized_sent)
                    #word_is_correct - for first word
                    error_type = self.check_pos_grammar(sent_count, bi_word_count, pwn, next_word,tokenized_sent,temp_error_struct, word_is_correct)
                    #print("ERROR TYPE: ", error_type )

                else:
                    #save_next = next_word 
                    #print("SEARCH: ",pwn,  next_word, word_is_correct)              
                    posible_words, possible_words_next = self.get_possible_correction_words(next_word, pwn, main_forms_checking_sent)
                    if len(possible_words_next) != 0:
                        #print("NO MATCH1: ",pwn,  next_word, word_is_correct, possible_words_next)
                        error_type, new_second_word = self.search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, possible_words_next, bi_gramm_words,tokenized_sent,temp_error_struct, word_is_correct)
                        #print("NEW_WORD: ", new_second_word)
                        next_word = new_second_word
                        #print("WORDS: ",next_word )
                    else:
                        #print("NO MATCH2: ",pwn,  next_word, word_is_correct, posible_words)
                        error_type, new_second_word = self.search_for_second_word(i, sent_count, bi_word_count, pwn, next_word, posible_words, bi_gramm_words,tokenized_sent,temp_error_struct, word_is_correct)
                        next_word = new_second_word
                    
                    #print("ERROR TYPE2: ", error_type, next_word)
                    self.update_temp_error_struct(pwn, new_second_word, error_type, temp_error_struct)
                if error_type == WORD_WITH_NO_MISTAKE:
                    break 
                  

            #print("\n\n\nAFTER_BREAK: ", temp_error_struct)       
            if temp_error_struct['error_type'] != 'NONE' and error_type != WORD_WITH_NO_MISTAKE and error_type != WORD_WITH_NO_MISTAKE:
                error_t = temp_error_struct['error_type']
                if error_t == SPELLING_AND_ORDER or error_t == SPELLING_MISTAKE or error_t == WORD_FORM_MISTAKE:
                    self.update_words_struct(sent_count, bi_word_count, temp_error_struct['first_word'], temp_error_struct['second_word'], error_t)
                    #print("\nWAWAWAWA: ", temp_error_struct['first_word'])
                    if temp_error_struct['first_word'] != END_TOKEN:
                        tokenized_sent[bi_word_count]  = temp_error_struct['first_word']
                    if temp_error_struct['second_word'] != END_TOKEN:
                        tokenized_sent[bi_word_count + 1] = temp_error_struct['second_word']
                else:
                    if error_t != WORD_WITH_NO_MISTAKE:
                        if error_type == TRANSLATION_MISTAKE:
                            if WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error']:
                                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], error_t)
                            if WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count + 1]['error']:
                                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], error_t)
                        else:
                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], error_t)
                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], error_t)
                       # else:
                            #self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], error_t)
                error_type = error_t
            if error_type != WORD_WITH_NO_MISTAKE and error_type != SPELLING_MISTAKE and self.word_error_struct[sent_count][bi_word_count]['word'] != END_TOKEN and self.word_error_struct[sent_count][bi_word_count + 1]['word'] != END_TOKEN:
                if WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error'] and WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count + 1]['error']:
                    corrected_sent = self.join_sent(tokenized_sent)
                    #print("corrected_sent: " , tokenized_sent)
                    tag = self.get_word_pos(corrected_sent)
                    #print("\n SENT: ", tokenized_sent)
                    #print("\n TAG: ", tag)
                    if not self.word_error_struct[sent_count][bi_word_count]['new']:
                        first_word = self.word_error_struct[sent_count][bi_word_count]['word']
                    else:
                        first_word = self.word_error_struct[sent_count][bi_word_count]['new']
                    if not self.word_error_struct[sent_count][bi_word_count + 1]['new']:
                        second_word = self.word_error_struct[sent_count][bi_word_count + 1]['word']
                    else:
                        second_word = self.word_error_struct[sent_count][bi_word_count + 1]['new']
                    tagsetRepo = repo.TagsetRepository(model.Tagset)
                    
                    #print("FIRST: ", self.word_error_struct[sent_count][bi_word_count])
                    #print("SECOND: ", self.word_error_struct[sent_count][bi_word_count + 1])
                    if first_word in tag.keys() and second_word in tag.keys():
                        tag1_id = tagsetRepo.get_tag_id(tag[first_word])
                        tag2_id = tagsetRepo.get_tag_id(tag[second_word])
                        is_grammarly_correct = 1
                        if tag1_id != -1 and tag2_id != -1:
                            bigramRepo = repo.BiGrammsRepository(model.BiGramms)
                            is_grammarly_correct = bigramRepo.get_combination(tag1_id, tag2_id)
                        
                        #print("GRAMMAR_CHECK: ", first_word, second_word, tag[first_word], tag[second_word], is_grammarly_correct)
                        if is_grammarly_correct == -1:
                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], GRAMMAR_MISTAKE)
                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], GRAMMAR_MISTAKE)
            #print("\nTEMP_STRUCT: ", temp_error_struct)
            ##print("CHECK: ", tokenized_sent)
            #print("\nSTRUCT: ", self.word_error_struct)

    def search_for_second_word(self, i, sent_count, bi_word_count, first_word, second_word_, possible_words, bi_gramm_words,tokenized_sent,temp_error_struct, first_word_is_correct):
        error_type = SPELLING_MISTAKE
        word_correct = SPELLING_MISTAKE

        #print("FIRST_SECOND: ", first_word, second_word_)
        #print("POSSIBLE WORDS IN ", possible_words)
        for second_word in possible_words:
            second_word_ = second_word
            
            if possible_words[second_word] == WORD_FORM_MISTAKE:
                #print("\nWORD FORM MISTAKE")
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
                ##print("\n\n\nTAG_WORD2: ", first_word, second_word)
                #skipped = 1
                #continue
            
            #print("NEW_comp2: ", new_word_comb, first_word_is_correct)
            if new_word_comb in self.bi_words_ethalon: 
                #print("\nSPELLING: ", new_word_comb),
                if first_word_is_correct != WORD_FORM_MISTAKE:
                    word_correct = SPELLING_MISTAKE
                else:
                    if WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error']:
                        word_correct = NOT_IN_ETHALON
                    else:
                        word_correct = SPELLING_MISTAKE 
                        #self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], SPELLING_MISTAKE)
                self.update_temp_error_struct(first_word, second_word, word_correct, temp_error_struct)   
            else:
                corrected_sent = self.join_sent(tokenized_sent)
                tag = self.get_word_pos(corrected_sent)
                pos_bi_gramm = self.build_new_pos_bi_gram(tag, first_word, second_word, sent_count, bi_word_count)
                #print("ELSE: ", pos_bi_gramm, self.bi_pos_ethalon)
            
                if word_correct !=  WORD_FORM_MISTAKE:
                    if first_word_is_correct != NOT_IN_ETHALON:
                        #print("\nSPELLING + WRONG_ORDER0: ", pos_bi_gramm, first_word, second_word)
                        word_correct = SPELLING_AND_ORDER
                        if TRANSLATION_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error']:
                            word_correct = SPELLING_MISTAKE
                    else:
                        #print("\nNOT ETHALON1: ", pos_bi_gramm, first_word, second_word)
                        word_correct = NOT_IN_ETHALON 
                else:
                    
                    #print("\nORDER: ", pos_bi_gramm, first_word, second_word, word_correct)
                    if first_word_is_correct != NOT_IN_ETHALON:
                        if first_word_is_correct == TRANSLATION_MISTAKE and pos_bi_gramm in self.bi_pos_ethalon:
                            word_correct = WORD_WITH_NO_MISTAKE
                        else:
                            word_correct = WRONG_ORDER   
             
                    else:
                        if pos_bi_gramm in self.bi_pos_ethalon:
                            if tag[first_word].startswith("V") or tag[second_word].startswith("V"):
                                 word_correct = WORD_FORM_MISTAKE
                            else:
                                word_correct = TRANSLATION_MISTAKE
                        else:
                            word_correct = NOT_IN_ETHALON                    
                
                self.update_temp_error_struct(first_word, second_word, word_correct, temp_error_struct)

            if possible_words[second_word] >= 0.81:
                break
            
            temp_error_struct['error_type'] = 'NONE'
            error_type = self.check_pos_grammar(sent_count, bi_word_count,first_word, second_word_, tokenized_sent, temp_error_struct, word_correct)

        if len(possible_words) == 0:  #no possible words to change with
            #print("NO_CHANGEEE", possible_words, second_word_)
            
            word_correct = NOT_IN_ETHALON
            save_word = second_word_

            if second_word_ in short_forms.keys():
                if short_forms[second_word_] in self.words_main_ethalon.keys():
                    word_correct = WORD_WITH_NO_MISTAKE
                    second_word_ = short_forms[second_word_]
                    self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word_
                    tokenized_sent[bi_word_count+1] = second_word_
            else:
                #print("EXc: ",second_word_, short_forms.values())
                if second_word_ in short_forms.values():
                    val_list = list(short_forms.values())
                    position = val_list.index(second_word_)
                    key_list = list(short_forms.keys())
                    second_word_ = key_list[position]
                    if second_word_ in self.words_main_ethalon.keys():
                        word_correct = WORD_WITH_NO_MISTAKE
                        #print("EXcaaa: ",second_word_)
                        self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word_
                        tokenized_sent[bi_word_count+1] = second_word_
                    else:
                        second_word_ = save_word
                    del val_list
                    del key_list

                error_type = self.check_pos_grammar(sent_count, bi_word_count, first_word, second_word_,tokenized_sent,temp_error_struct, word_correct)
        return error_type, second_word_

    def check_pos_grammar(self, sent_count, bi_word_count, first_word, second_word, tokenized_sent, temp_error_struct, word_correct):
        new_bi_gramm = first_word + " " + second_word
        #print("NEW_BI: ", new_bi_gramm, self.bi_words_ethalon)
        error_type = SPELLING_MISTAKE
        if new_bi_gramm in self.bi_words_ethalon:
            if word_correct == SPELLING_MISTAKE:
                #FRONT -4
                #print("\n + SPELLING: ", new_bi_gramm)
                if first_word in self.words_main_ethalon.keys() and WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count + 1]['error'] and second_word != END_TOKEN:
                    error_type = NOT_IN_ETHALON
                    temp_error_struct['error_type'] = error_type
                else:
                    error_type = SPELLING_MISTAKE
            else:
                #print("\n NO_MISTAKE: ", new_bi_gramm)
                if WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error'] and second_word != END_TOKEN:
                        error_type = NOT_IN_ETHALON
                else:         
                    error_type = word_correct
        else:
            corrected_sent = self.join_sent(tokenized_sent)

            ##print("corrected_sent: " , tokenized_sent)
            tag = self.get_word_pos(corrected_sent)

            #print("\n SENT: ", tokenized_sent)
            #print("\n TAG: ", tag)
            
            pos_bi_gramm = self.build_new_pos_bi_gram(tag, first_word, second_word, sent_count, bi_word_count)
                
            if pos_bi_gramm in self.bi_pos_ethalon:
                #print("ALL_Coo: ", first_word, second_word, pos_bi_gramm, word_correct)
                #print("POS ETHALON: ", self.bi_pos_ethalon)
                if word_correct == WORD_WITH_NO_MISTAKE:
                    #print("\nWRONG ORDER1: ", new_bi_gramm)
                    if TRANSLATION_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error']:
                        error_type = WRONG_ORDER
                if word_correct == SPELLING_MISTAKE:
                    #print("\nSPELLING + WRONG_ORDER1: ", new_bi_gramm)
                    error_type = SPELLING_AND_ORDER
                if word_correct == WORD_FORM_MISTAKE:
                    if tag[first_word].startswith("V") or tag[first_word] == 'MD':
                        if WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error'] and tag[first_word] == 'MD':
                            error_type = NOT_IN_ETHALON
                        else:
                            error_type = WORD_FORM_MISTAKE
                    else:
                        error_type = WRONG_ORDER

                if (word_correct == NOT_IN_ETHALON or word_correct == TRANSLATION_MISTAKE) and second_word != END_TOKEN:
                    #print("\nnTRANSLATION_WORD: ",error_type, new_bi_gramm, tag[first_word] , tag[second_word], self.bi_pos_ethalon)
                    #get possible translation
                   
                    if word_correct == TRANSLATION_MISTAKE:
                        if first_word not in self.words_main_ethalon.keys() and second_word in self.words_main_ethalon.keys():
                            error_type = TRANSLATION_MISTAKE 
                    else:
                        if NOT_IN_ETHALON in self.word_error_struct[sent_count][bi_word_count]['error'] and WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error']:
                            error_type = NOT_IN_ETHALON
                        if tag[first_word].startswith("V") or tag[second_word].startswith("V") or tag[first_word] == 'MD' or tag[second_word] == 'MD':
                            #print("\nFORS_SEC: ", first_word, second_word, self.word_error_struct[sent_count][bi_word_count]['word'],  self.word_error_struct[sent_count][bi_word_count + 1]['word'])
                            if (tag[first_word].startswith("V") or tag[second_word] == 'MD') and first_word not in self.words_main_ethalon.keys():
                                error_type = WORD_FORM_MISTAKE
                            #print("\nFORS_SEC2: ", second_word, self.words_main_ethalon.keys())
                            if (tag[second_word].startswith("V") or tag[second_word] == 'MD') and second_word not in self.words_main_ethalon.keys():
                                error_type = WORD_FORM_MISTAKE
                                if tag[second_word] == 'MD':
                                    error_type = NOT_IN_ETHALON
                            else:
                                #print("AA2")
                                error_type = TRANSLATION_MISTAKE   
                        else:
                            #print("AA1")
                            error_type = TRANSLATION_MISTAKE
                    
                    if first_word not in self.words_main_ethalon.keys() and error_type == TRANSLATION_MISTAKE:
                        if bi_word_count - 2 in self.word_error_struct[sent_count].keys():

                            if NOT_IN_ETHALON in  self.word_error_struct[sent_count][bi_word_count]['error'] and WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error']:
                                if NOT_IN_ETHALON in self.word_error_struct[sent_count][bi_word_count - 1]['error'] and NOT_IN_ETHALON not in self.word_error_struct[sent_count][bi_word_count - 2]['error']:
                                    if not self.word_error_struct[sent_count][bi_word_count - 1]['new']:
                                        first_word = self.word_error_struct[sent_count][bi_word_count - 1]['word']
                                    else:
                                        first_word = self.word_error_struct[sent_count][bi_word_count - 1]['new']
                                    if not self.word_error_struct[sent_count][bi_word_count]['new']:
                                        second_word = self.word_error_struct[sent_count][bi_word_count]['word']
                                    else:
                                        second_word = self.word_error_struct[sent_count][bi_word_count]['new']
                                    temp_tokenized_sent = tokenized_sent
                                    temp_tokenized_sent[bi_word_count - 1] = first_word
                                    temp_tokenized_sent[bi_word_count] = second_word
                                    corrected_sent_temp = self.join_sent(temp_tokenized_sent)

                                    tag_temp = self.get_word_pos(corrected_sent_temp)
                                    pos_bi_gramm_temp = self.build_new_pos_bi_gram(tag_temp, first_word, second_word, sent_count, bi_word_count)
                                    #print("DELETE_-4: " , pos_bi_gramm_temp, first_word, second_word)
                                    if pos_bi_gramm_temp in self.bi_pos_ethalon:
                                        self.word_error_struct[sent_count][bi_word_count - 1]['error'].remove(NOT_IN_ETHALON)
                                        self.word_error_struct[sent_count][bi_word_count]['error'].remove(NOT_IN_ETHALON)
                                        self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count - 1]['error'], TRANSLATION_MISTAKE)
                                    else:
                                        if first_word in self.words_main_ethalon.keys():
                                            self.word_error_struct[sent_count][bi_word_count - 1]['error'].remove(NOT_IN_ETHALON)
                                            self.word_error_struct[sent_count][bi_word_count]['error'].remove(NOT_IN_ETHALON)
                                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], WRONG_ORDER)
                                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count - 1]['error'], WRONG_ORDER)

                    


            else:
                #print("ALL_Coo22: ", first_word, second_word, pos_bi_gramm, word_correct, self.bi_pos_ethalon)
                if word_correct == NOT_IN_ETHALON:
                    #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) ", new_bi_gramm, pos_bi_gramm)
                    if (tag[first_word].startswith("V") or tag[first_word] == 'MD') and second_word not in self.words_main_ethalon.keys():
                        #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 1", tag[first_word], second_word)
                        error_type = NOT_IN_ETHALON
                    else:
                        if second_word == END_TOKEN:
                            tag[second_word] = END_TOKEN
                        if (tag[second_word].startswith("V") or tag[second_word] == 'MD') and first_word not in self.words_main_ethalon.keys():
                            #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 2", tag[second_word], first_word)
                            error_type = NOT_IN_ETHALON
                            
                        else:
                            #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 3", tag[second_word], first_word)
                            if NOT_IN_ETHALON not in self.word_error_struct[sent_count][bi_word_count]['error'] and NOT_IN_ETHALON not in self.word_error_struct[sent_count][bi_word_count + 1]['error']:
                                if tag[first_word].startswith("V") or tag[second_word].startswith("V") or tag[first_word] == 'MD' or tag[second_word] == 'MD':
                                    if WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error']:
                                        error_type = NOT_IN_ETHALON
                                        #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 3.1", tag[second_word], first_word)
                                    else:
                                        if first_word in self.words_main_ethalon.keys() and (tag[second_word].startswith("V") or tag[second_word] == 'MD'):
                                            #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 3.23", tag[second_word], first_word)
                                            error_type = NOT_IN_ETHALON
                                        else:
                                            #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 3.2", tag[second_word], first_word)
                                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], NOT_IN_ETHALON)
                                            error_type = WORD_FORM_MISTAKE
                                else:
                                    #print("PROBABLY_TRANSLATE (NOT_IN_ETHALON) 3.3", tag[second_word], tag[second_word])
                                    if (not tag[first_word].startswith("V") or tag[first_word] != 'MD') and (not tag[second_word].startswith("V") or tag[second_word] != 'MD'):
                                        error_type = NOT_IN_ETHALON
                                    else:
                                        error_type = WORD_FORM_MISTAKE
                            else:
                                error_type = NOT_IN_ETHALON
                else:
                    if word_correct == WORD_WITH_NO_MISTAKE and word_correct != WORD_FORM_MISTAKE: #words are correct from the begginig:
                        #print("\nWRONG ORDER2: ", new_bi_gramm, pos_bi_gramm)
                        error_type = WRONG_ORDER
                    else:
                        if word_correct != WORD_FORM_MISTAKE and second_word != END_TOKEN:
                            if word_correct == TRANSLATION_MISTAKE:
                                if second_word in self.words_main_ethalon.keys() and TRANSLATION_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error']:
                                    error_type = WRONG_ORDER
                                else:
                                    error_type = NOT_IN_ETHALON
                                #print("\nTRANSALATION: ", new_bi_gramm, pos_bi_gramm, temp_error_struct)
                            else:
                                #print("\nSPELLING + WRONG_ORDER2: ", new_bi_gramm, pos_bi_gramm, self.word_error_struct[sent_count][bi_word_count]['new'], self.word_error_struct[sent_count][bi_word_count]['error'])
                                if self.word_error_struct[sent_count][bi_word_count]['new'] and WORD_FORM_MISTAKE in self.word_error_struct[sent_count][bi_word_count]['error']:
                                    error_type = NOT_IN_ETHALON
                                    temp_error_struct['error_type'] = error_type
                                    #print("\nSPELLING + WRONG_ORDER2.1:" )
                                else:
                                    error_type = SPELLING_AND_ORDER
                        else:
                            #print("\n WRONG_ORDER3: ", new_bi_gramm, pos_bi_gramm,)
                            #print("\n", self.pos_ethalon)
                            if word_correct == WORD_FORM_MISTAKE and second_word != END_TOKEN:
                                ethalon_pos = self.check_if_word_tag_from_ethalon(second_word)
                                #print("\n WRONG_ORDER31: ", second_word, tag[second_word], ethalon_pos)
                                if second_word in self.words_main_ethalon.keys() and (tag[second_word].startswith("V") or tag[second_word] == 'MD' or ethalon_pos.startswith("V") or ethalon_pos == 'MD') :
                                    error_type = WRONG_ORDER
                                else:
                                    #print("\n WRONG_ORDER32: ", second_word, tag[second_word], ethalon_pos)
                                    if second_word in self.words_main_ethalon.keys():
                                        ethalon_pos_first = self.check_if_word_tag_from_ethalon(first_word)
                                        if ethalon_pos_first == 'NNNN':
                                            ethalon_pos_first = tag[first_word]
                                        if ethalon_pos_first in self.pos_ethalon.values():
                                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], WRONG_ORDER)
                                            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], WRONG_ORDER)
                                    error_type = NOT_IN_ETHALON
                            else:
                                if tag[first_word].startswith("V") or tag[first_word] == 'MD' and second_word != END_TOKEN:
                                    if second_word != END_TOKEN:
                                        error_type = WORD_FORM_MISTAKE
                                    else:
                                        error_type = WRONG_ORDER
                                else:
                                    error_type = WRONG_ORDER

            if error_type == GRAMMAR_MISTAKE or error_type == NOT_IN_ETHALON or error_type == WORD_FORM_MISTAKE:
                if tag[first_word].startswith("V") or tag[first_word] == 'MD':
                    if first_word not in self.words_main_ethalon.keys():
                        self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], WORD_FORM_MISTAKE)
                if tag[second_word].startswith("V") or tag[second_word] == 'MD':
                    if second_word not in self.words_main_ethalon.keys():
                        self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], WORD_FORM_MISTAKE)
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
                    #print("sent: ", sent, index+1)
                    #print("ET_NETXT: ", word_from_ethalon, cur_word , next_word)
                    if word_from_ethalon == next_word and index != sent_len:
                        ethalon_word = sent[index+1]
                        if ethalon_word not in word_next:
                            if ethalon_word in self.words_main_ethalon.keys():
                                #print("HERERERE: ", ethalon_word, cur_word)
                                ##print(self.words_main_ethalon)
                                #print("HERERERE1: ", self.words_main_ethalon[ethalon_word], main_form_checking[cur_word])
                                if ethalon_word in self.words_main_ethalon.keys() and cur_word in main_form_checking.keys():
                                    if self.words_main_ethalon[ethalon_word] != main_form_checking[cur_word]:
                                        self.word_possible_root_precess(ethalon_word, cur_word, word_next, {})
                                        #print("WHATATATA: ", word_next)
                                    else:
                                        #print("SAME FORMS11???: ", self.words_main_ethalon[ethalon_word], main_form_checking[cur_word])
                                        self.check_for_short_forms(ethalon_word, cur_word, word_next)
                            
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
                                self.check_for_short_forms(word_from_ethalon, cur_word, words)
 
                   

        #print("\n\n\nSEARCH RES: ", word_next)
        #print("\n\n\nSEARCH RESw: ", words)
        words = self.sort_dict(words)
        word_next = self.sort_dict(word_next)
        
        return words, word_next

    def word_possible_root_precess(self, ethalon_word, cur_word, word_next_arr, words_arr):
        ratio = self.levenshtein_ratio_and_distance(ethalon_word, cur_word, ratio_calc = True)
        #print("RATIO: ", ratio)
        roots_change = 0
        if ratio < 0.75:
            root_cur =  self.rootFinder.stem(cur_word)
            root_eth =  self.rootFinder.stem(ethalon_word)
            #print("ROOTS: ", root_cur, root_eth, ratio)
            if len(root_cur) > len(root_eth):
                new_root = root_cur[:len(root_cur) - (len(root_cur) - len(root_eth))]
                if len(new_root) >= 3:
                    root_cur = new_root
                    roots_change = 1
            ratio_root = self.levenshtein_ratio_and_distance(root_cur, root_eth, ratio_calc = True)
            #print("HERERERE_RATIO: ", ratio_root, root_cur, root_eth, ratio)
            if ratio_root >= 0.75 and ratio > 0.5:
                word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
            else:
                if ratio_root >= 0.5 and len(cur_word) <= 3: #for short words like do, ate ...
                    #print("\n\nELSE2.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                    if self.pos_ethalon[ethalon_word].startswith("V") or self.pos_ethalon[ethalon_word] == 'MD':
                        #print("\n\nELSE3: ", self.pos_ethalon[ethalon_word])
                        tags = self.posTagger.tag(cur_word)
                        for tag_info in tags:
                            tag = tag_info.split(" ")
                            _tag = tag[0].split()
                            #print("\n\nELSE4: ", _tag)
                            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                if _tag[1].startswith("V") or _tag[1] == 'MD':
                                    if ratio > 0.60 and ratio_root > 0.4 and len(cur_word) >= 2:
                                        word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
                                else:
                                    if ratio > 0.60 and ratio_root > 0.65 and len(cur_word) >= 2:
                                        word_next_arr.update({ethalon_word:ratio})
                    else:
                        tags = self.posTagger.tag(cur_word)
                        for tag_info in tags:
                            tag = tag_info.split(" ")
                            _tag = tag[0].split()
                            if not roots_change:
                                root_cur =  self.rootFinder.stem(cur_word)
                                root_eth =  self.rootFinder.stem(ethalon_word)
                                ratio_root_temp = self.levenshtein_ratio_and_distance(root_cur, root_eth, ratio_calc = True)
                            #print("COMPARE POS: ", self.pos_ethalon[ethalon_word], _tag[1])
                            if not _tag[1].startswith("V") and _tag[1] != 'MD' and ratio_root_temp >= 0.60 and ratio > 0.65 and len(cur_word) > 2:
                                word_next_arr.update({ethalon_word:ratio})
                else:
                    tags = self.posTagger.tag(cur_word)
                    for tag_info in tags:
                        tag = tag_info.split(" ")
                        _tag = tag[0].split()
                        if not roots_change:
                            root_cur =  self.rootFinder.stem(cur_word)
                            root_eth =  self.rootFinder.stem(ethalon_word)
                            ratio_root = self.levenshtein_ratio_and_distance(root_cur, root_eth, ratio_calc = True)
                        #print("COMPARE POS1: ", self.pos_ethalon[ethalon_word], _tag[1], ratio_root, ratio, root_cur, root_eth)
                        if not _tag[1].startswith("V") and _tag[1] != 'MD' and ratio_root >= 0.60 and ratio > 0.65 and len(cur_word) > 2:
                            word_next_arr.update({ethalon_word:ratio})
                            #print("IN")

                                    
        if ratio >= 0.75:
            root1 = self.rootFinder.stem(cur_word)
            root2 = self.rootFinder.stem(ethalon_word)
            if root1 != root2:
                words_rates = words_arr.values()
                if len(words_arr) == 0:
                    max_rate = -10
                else:
                    max_rate = max(words_rates)
                
                if ratio > 0.65 and ratio >= max_rate:
                    ratio_root = self.levenshtein_ratio_and_distance(root1, root2, ratio_calc = True)
                    if ratio_root > 0.9 and ratio < 0.85:
                        word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE}) 
                    else:
                        word_next_arr.update({ethalon_word:ratio})
                    #print("IAGAGAGAGAGAGAGAG", word_next_arr, root1, root2)
                #print("HERERERE_RATIO_ИН_ИН: ", cur_word, ethalon_word, ratio, ratio_root, max_rate)
            else:
               #print("WHY HERE: ", root1, root2)
               word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE}) 

            #print("\n\nELSE1: ", ethalon_word, cur_word, self.pos_ethalon.keys())
            if ethalon_word in self.pos_ethalon.keys():
                keep_going = 1
                if ethalon_word in word_next_arr:
                    if word_next_arr[ethalon_word] >= 0.8:
                        keep_going = 0
                    if keep_going:     
                        #print("\n\nELSE1.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                        if self.pos_ethalon[ethalon_word].startswith("V"):
                            #print("\n\nELSE2: ", self.pos_ethalon[ethalon_word])
                            tags = self.posTagger.tag(cur_word)
                            for tag_info in tags:
                                tag = tag_info.split(" ")
                                _tag = tag[0].split()
                                #print("\n\nELSE3: ", _tag)
                                if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                    if _tag[1].startswith("V") or _tag[1] == 'MD':
                                        word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
        ##print("MID RES: ", word_next_arr)

    def check_for_short_forms(self, word_from_ethalon, cur_word, possible_words_arr):
        if word_from_ethalon in short_forms.keys() or word_from_ethalon in short_forms.values():
            is_form_mistake = 1
            if word_from_ethalon in short_forms.keys():
                if short_forms[word_from_ethalon] == cur_word:
                    possible_words_arr.update({word_from_ethalon: WORD_WITH_NO_MISTAKE})
                    is_form_mistake = 0
            else:
                if word_from_ethalon in short_forms.values():
                    val_list = list(short_forms.values())
                    position = val_list.index(word_from_ethalon)
                    key_list = list(short_forms.keys())
                    if key_list[position] == cur_word:
                        possible_words_arr.update({word_from_ethalon: WORD_WITH_NO_MISTAKE})
                        is_form_mistake = 0
            ratio_w = self.levenshtein_ratio_and_distance(word_from_ethalon, cur_word, ratio_calc = True)
            #print("MAYBE HERE : ", word_from_ethalon, cur_word, ratio_w)
            if is_form_mistake:
                ratio_w = self.levenshtein_ratio_and_distance(word_from_ethalon, cur_word, ratio_calc = True)
                if ratio_w > 0.3:
                    if len(word_from_ethalon) <= 3:
                        if ratio_w > 0.43:
                            possible_words_arr.update({word_from_ethalon: WORD_FORM_MISTAKE}) 
                    else:
                        possible_words_arr.update({word_from_ethalon: WORD_FORM_MISTAKE}) 
        else:
            ratio_w = self.levenshtein_ratio_and_distance(word_from_ethalon, cur_word, ratio_calc = True)
            #print("MAYBE there : ", word_from_ethalon, cur_word, ratio_w)
            if ratio_w > 0.3:
                if len(word_from_ethalon) <= 3:
                    if ratio_w > 0.43:
                        possible_words_arr.update({word_from_ethalon: WORD_FORM_MISTAKE}) 
                else:
                    possible_words_arr.update({word_from_ethalon: WORD_FORM_MISTAKE})

    def check_for_verbs(self, ethalon_word, cur_word, word_next_arr):
        #print("\n\nELSE1: ", ethalon_word, cur_word, self.pos_ethalon.keys())
        if ethalon_word in self.pos_ethalon.keys():
            keep_going = 1
            if ethalon_word in word_next_arr:
                if word_next_arr[ethalon_word] >= 0.8:
                    keep_going = 0
                if keep_going:     
                    #print("\n\nELSE1.1: ", ethalon_word, self.pos_ethalon[ethalon_word], self.pos_ethalon.keys())
                    if self.pos_ethalon[ethalon_word].startswith("V"):
                        #print("\n\nELSE2: ", self.pos_ethalon[ethalon_word])
                        tags = self.posTagger.tag(cur_word)
                        for tag_info in tags:
                            tag = tag_info.split(" ")
                            _tag = tag[0].split()
                            #print("\n\nELSE3: ", _tag)
                            if _tag[1] != 'SENT' and _tag[1] not in my_punctuation:
                                if _tag[1].startswith("V") or _tag[1] == 'MD':
                                    word_next_arr.update({ethalon_word: WORD_FORM_MISTAKE})
    def update_words_struct(self, sent_count, bi_word_count, first_word, second_word, error_type):
        errors = error_type
        if error_type == SPELLING_AND_ORDER:
            errors = SPELLING_MISTAKE
            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], WRONG_ORDER)
            self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], WRONG_ORDER)

        #print("CHECK1_CHECK1: ", self.word_error_struct[sent_count][bi_word_count]['word'], first_word, error_type )
        if self.word_error_struct[sent_count][bi_word_count]['word'] != first_word and not self.word_error_struct[sent_count][bi_word_count]['new'] and first_word != END_TOKEN: 
            self.word_error_struct[sent_count][bi_word_count]['new'] = first_word
            if error_type not in self.word_error_struct[sent_count][bi_word_count]['error']:
                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count]['error'], errors)
        
        #print("CHECK2_CHECK2: ", self.word_error_struct[sent_count][bi_word_count + 1]['word'], second_word)
        if self.word_error_struct[sent_count][bi_word_count + 1]['word'] != second_word and not self.word_error_struct[sent_count][bi_word_count + 1]['new'] and second_word != END_TOKEN: 
            self.word_error_struct[sent_count][bi_word_count + 1]['new'] = second_word
            if error_type not in self.word_error_struct[sent_count][bi_word_count + 1]['error']:
                self.append_if_not_exist(self.word_error_struct[sent_count][bi_word_count + 1]['error'], errors)
        #print("STRUCT_TEMP: ", self.word_error_struct)


    def update_temp_error_struct(self, first_word, second_word, error_type, temp_error_struct):
        #print("TEMP_struct_IN: ", temp_error_struct)
        if temp_error_struct['error_type'] == 'NONE' or error_type == WORD_FORM_MISTAKE or error_type == GRAMMAR_MISTAKE:
            temp_error_struct['first_word'] = first_word
            temp_error_struct['second_word'] = second_word
            temp_error_struct['error_type'] = error_type
       
        #print("TEMP_struct_OUT: ", temp_error_struct)

    def update_structs(self,error_type, first_word, second_word, sent_count, bi_word_count, temp_error_struct):
        to_break = 0
        if error_type == SPELLING_MISTAKE or error_type == WORD_FORM_MISTAKE or error_type == GRAMMAR_MISTAKE:
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

    def check_if_word_tag_from_ethalon(self, check_word):
        ethalon_pos = "NNNN"
        for key in self.pos_ethalon.keys():
            #print("KEY: ", key, check_word)
            if check_word == key:
                ethalon_pos = self.pos_ethalon[key]
                break
        return ethalon_pos

    def process_checking(self, ethalons, checking_sents):
        #print("\n\nETHALONS: ", ethalons)
        self.ethalon_info_prepare(ethalons)
        self.prepare_checking_sents(checking_sents)
        corrected_sent= self.process_mistakes()
        corrected_sent = self.remove_end_tags_corrected_sents(corrected_sent)
        return self.word_error_struct, error_explain, corrected_sent

    def remove_end_tags_corrected_sents(self, sents):
        corr_sents = ""
        for sent in sents:
            #print(sent)
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
            if word != END_TOKEN:
                if word.startswith("'"):
                    sent += word
                else:
                    sent += " " + word
        return sent

    def build_new_pos_bi_gram(self, tag, first_word, second_word, sent_count, bi_word_count):
        pos_bi_gramm = ""
        ethalon_pos_first = self.check_if_word_tag_from_ethalon(first_word)
        ethalon_pos_second = self.check_if_word_tag_from_ethalon(second_word)
        if ethalon_pos_first != 'NNNN' and WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count]['error']:
            tag[first_word] = ethalon_pos_first
        if ethalon_pos_second != 'NNNN'and WORD_FORM_MISTAKE not in self.word_error_struct[sent_count][bi_word_count+1]['error']:
            tag[second_word] = ethalon_pos_second
        if second_word == END_TOKEN:
            pos_bi_gramm = tag[first_word] + " " + END_TOKEN
        else:
            if first_word == END_TOKEN:
                pos_bi_gramm =  END_TOKEN + " " + tag[second_word]
            else:
                pos_bi_gramm = tag[first_word] + " " + tag[second_word]
        return pos_bi_gramm

    def get_word_tag(self, tag, word):
        word_tag = ""
        if word == END_TOKEN:
            word_tag = END_TOKEN
        else:
            word_tag = tag[word]
        return word_tag
           
    def reset(self):
        self.ethalon_sents = []
        self.checking_sents = []
        self.words_main_ethalon = dict()
        self.bi_words_ethalon = []
        self.bi_pos_ethalon = dict()
        self.nsubjs_ethalon = []
        self.auxs_ethalon = []
        self.pos_ethalon = dict()
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