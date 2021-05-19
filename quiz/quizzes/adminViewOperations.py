from .grammar.lang_abr import languages, abr_lang 
from quizzes.models import Languages, Tagset, BiGramms, TriGramms, LearnSets
import quizzes.repositories as repo
from .grammar.Trainer import Trainer, train_packet

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone

import quizzes.serializers as ser
from rest_framework.renderers import JSONRenderer


SAVE_TAG = 100
BI_GRAMM_LEN = 2
TRI_GRAMM_LEN = 3


def fill_languages():

    langRepo = repo.LanguagesRepository(Languages)
    if langRepo.is_empty():
        for abr in abr_lang:
            langRepo.add_lang(abr_lang[abr], abr)
    else:
        all_lang = langRepo.get_all()
        if len(all_lang) != len(abr_lang):
            copy_lang = abr_lang
            for lang in all_lang:
                if lang.abr in copy_lang.keys():
                    del copy_lang[lang.abr]
            for abr in copy_lang:
                langRepo.add_lang(copy_lang[abr], abr) 

            
def fill_LearnSets():
    lsRepo = repo.LearnSetsRepository(LearnSets)
    if lsRepo.is_empty():
        langRepo = repo.Languages(Languages)
        for abr in train_packet:
            l_id = langRepo.get_record_by_abr(abr)
            if l_id != -1:
                for lset in train_packet[abr]:
                    lsRepo.add_set(lset, l_id[0].id)
                    #print(lset, abr)

def train_tags(lang, train_set, lang_query, user_id):
    tr = Trainer(lang, train_set, user_id)
    unique_bigrams, unique_trigrams = tr.get_all_pos()
    tagsetRepo = repo.TagsetRepository(Tagset)
    if tagsetRepo.is_empty(lang_query.id):
        for tag in tr.get_tag_types():
            tagsetRepo.add_tag(tag, lang_query.id)
                    
    else:
        for tag in tr.get_tag_types():
                    
            tag_exists = tagsetRepo.get_tag_id(tag)
            if tag_exists == -1:
                tagsetRepo.add_tag(tag, lang_query.id)
    return unique_bigrams, unique_trigrams

def bi_tags_model(lang, train_set, unique_bigrams, lang_query, learnSet):
    tags_id = dict()
    tagsetRepo = repo.TagsetRepository(Tagset)
    bigramRepo = repo.BiGrammsRepository(BiGramms)
    for bi in unique_bigrams:
        comb = bi.split(" ")
        if len(comb) == BI_GRAMM_LEN:
            tags_ids = []
            for tag in comb:
                if tag not in tags_id.keys():
                    tag_db = tagsetRepo.get_tag(tag)   
                    if tag_db != -1:
                        tag_db = tag_db[0]
                        tags_ids.append(tag_db)
                        if unique_bigrams[bi] > SAVE_TAG:
                            tags_id[tag] = tag_db
                else:
                    tags_ids.append(tags_id[tag])
                            
                if len(tags_ids) == BI_GRAMM_LEN:
                    print(tags_ids)
                    comb_exists = bigramRepo.get_combination(tags_ids[0].id, tags_ids[1].id)
                    if comb_exists == -1:
                        bigramRepo.add_tag_combination(tags_ids[0], tags_ids[1], unique_bigrams[bi], lang_query.id, learnSet[0].id)
                    else:
                        bigramRepo.update_combination_freq(comb_exists[0].id, unique_bigrams[bi])
         


                    
def tri_tags_model(lang, train_set, unique_trigrams, lang_query, learnSet):
    tags_id = dict()
    tagsetRepo = repo.TagsetRepository(Tagset)
    trigramRepo = repo.TriGrammsRepository(TriGramms)
    for tri in unique_trigrams:
        comb = tri.split(" ")
        if len(comb) == TRI_GRAMM_LEN:
            tags_ids = []
            for tag in comb:
                if tag not in tags_id.keys():
                    tag_db = tagsetRepo.get_tag(tag)   
                    if tag_db != -1:
                        tag_db = tag_db[0]
                        tags_ids.append(tag_db)
                        if unique_trigrams[tri] > SAVE_TAG:
                            tags_id[tag] = tag_db
                else:
                    tags_ids.append(tags_id[tag])
                            
                if len(tags_ids) == TRI_GRAMM_LEN:
                    print(tags_ids)
                    comb_exists = trigramRepo.get_combination(tags_ids[0].id, tags_ids[1].id, tags_ids[2].id)
                    if comb_exists == -1:
                        trigramRepo.add_tag_combination(tags_ids[0], tags_ids[1], tags_ids[2], unique_trigrams[tri], lang_query.id, learnSet[0].id)
                    else:
                        trigramRepo.update_combination_freq(comb_exists[0].id, unique_trigrams[tri])
        


def train_tags_model(lang, train_set, user_id):
    langRepo = repo.LanguagesRepository(Languages)
    lsRepo = repo.LearnSetsRepository(LearnSets)

    lang_query = langRepo.get_language(lang)
    return_status = False
    if lang_query != -1:
        lang_query = lang_query[0]
        lang_id = lang_query.id
        learnSet = lsRepo.get_set(train_set, lang_id)

        if len(learnSet) != 0:
            unique_bigrams, unique_trigrams = train_tags(lang, train_set, lang_query, user_id)
            if len(unique_bigrams) != 0:
                unique_bigrams = sorted(unique_bigrams.items(), key=lambda x: x[1], reverse=True)
                unique_bigrams= {k:v for k,v in unique_bigrams}
                #unique_trigrams = sorted(unique_trigrams.items(), key=lambda x: x[1], reverse=True)
                #unique_trigrams= {k:v for k,v in unique_trigrams}
            #if packet exists: no no no or if session processed != 0 

            if len(unique_bigrams) != 0 or len(unique_trigrams) != 0:
                bi_tags_model(lang, train_set, unique_bigrams, lang_query, learnSet)
                #tri_tags_model(lang, train_set, unique_trigrams, lang_query, learnSet)
                return_status = True
          
    return return_status

    


def get_progress(user_id):
    key = 'id_' + str(user_id)
    for session in Session.objects.filter(expire_date__gt=timezone.now()):
        store = SessionStore(session_key=session.session_key)
        if int(store.get('_auth_user_id')) == user_id:
            if key in store:
                delit = int(store[key]['total'])
                if delit != 0: 
                    #print("BEEE GOOOD: ", store[key]['processed'], store[key]['total'])
                    return int(store[key]['processed']) / int(store[key]['total']), store[key]['corpus']
                
    return 0, ''