from nltk.corpus import brown
from quizzes.grammar.Tokenizer import Tokenizer, END_TOKEN
from quizzes.grammar.PoSTagger import PoSTagger
from quizzes.grammar.lang_abr import lang_to_abr
from corus import load_lenta
from quizzes.grammar.helper import process_sent
import sys
from pathlib import Path
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
import ast

train_packet = {
	'en': ['brown'],
	'ru': ['lenta-ru-news.csv.gz']
}

RU_RECORDS = 5000
SHOW_AFTER = 200
class Trainer:
	def __init__(self, lang = 'en', train_set = "All", user_id = 0, session = True):
		self.lang = lang_to_abr(lang)
		self.tag_types = [END_TOKEN]
		self.BASE_DIR = Path(__file__).resolve(strict=True).parents[1]
		if train_set == "All":
			self.train_sets = train_packet[self.lang]
		else:
			self.train_sets = [train_set]
		self.user_id = user_id
		self.session = session

	def get_tag_types(self):
		self.tag_types.sort()
		return self.tag_types

	def get_all_pos(self):
		if self.session:
			store = ""
			key = 'id_' + str(self.user_id)
			for session in Session.objects.filter(expire_date__gt=timezone.now()):
				store = SessionStore(session_key=session.session_key)
				if int(store.get('_auth_user_id')) == self.user_id:
					if key not in store:
						store[key] = {'processed': -1, 'total': 0, 'corpus': self.train_sets[0]}

		unique_bigrams = dict()
		unique_trigrams = dict()
		posTagger = PoSTagger(self.lang)
		tok = Tokenizer(lang=self.lang)

		for train_file in self.train_sets:
			# i_start, i_end
			if self.session:
				#print("TTTEEESSSSTTTT: ", store[key]['processed'])
				if store[key]['processed'] != -1:
					print("_BREAK__BREAK__BREAK__BREAK__BREAK__BREAK__BREAK_")
					break

				store[key]['processed'] = 0
				store.save()

				'''
				for tt in self.tag_types:
					if tt not in DB:
						save tag in db
				clear self.tag_types

				for bigramm in unique_bigrams:
					if bigramm not in DB:
						save bigramm in db
					else:
						upgrade bigram freq in db
				clear bigramm
				'''
			path = str(self.BASE_DIR) + '\\grammar\\data\\' + train_file
			if self.lang == 'en':
				sents = [' '.join(sent).replace(':', '').replace('``', '').replace("''", '').replace('`', "'").split() for sent in brown.sents()]
				if self.session:
					store[key]['total'] = len(sents)
				for i in range(len(sents)):
					if self.session:
						if (i + 1) % SHOW_AFTER == 0:
							if i != 0:
								store[key]['processed'] = int(store[key]['processed']) + SHOW_AFTER
								store.save()
								print("STORE ",i, ": ", store[key])
					#if i == 2:
					#	break
					cur_sent = ' '.join(sents[i])
					self.tag_types, temp = process_sent(cur_sent, self.tag_types, posTagger, make_all_lower = True)
					unique_bigrams = tok.generate_different_ngrams([temp], 2, unique_bigrams)
					#unique_trigrams = tok.generate_different_ngrams([temp], 3, unique_trigrams)
					#print(i)
							
						
			if self.lang == 'ru':
				records = load_lenta(path)
				if self.session:
					store[key]['total'] = RU_RECORDS
				rec_count = 0
				print(RU_RECORDS)
				for record in records:

					if self.session:
						if (rec_count + 1) % SHOW_AFTER == 0:
							if rec_count != 0:
								store[key]['processed'] = int(store[key]['processed']) + SHOW_AFTER
								store.save()
								print("STORE ",rec_count, ": ", store[key])
					#print(rec_count)
					if rec_count == RU_RECORDS:
						break
					
					rec_count +=1
					tokenized_sent = tok.tokenize_sent(record.text)
					for sent in tokenized_sent:
						self.tag_types, temp = process_sent(sent, self.tag_types, posTagger, make_all_lower = True)
						unique_bigrams = tok.generate_different_ngrams([temp], 2, unique_bigrams)
						#unique_trigrams = tok.generate_different_ngrams([temp], 3, unique_trigrams)			
		return unique_bigrams, unique_trigrams

	def get_n_grams(self):
		tok = Tokenizer(lang=self.lang)

		bi_grams = tok.generate_different_ngrams(self.tag_sents, 2)

		bi_grams = dict(sorted(bi_grams.items(), key=lambda item: item[1], reverse=True))
		print(bi_grams)
		print(len(bi_grams))

	def get_all_tag_types(self):
		self.tag_types.sort()
		for tag in self.tag_types:
			print(tag)
