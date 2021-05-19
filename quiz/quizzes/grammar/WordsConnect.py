import spacy
from quizzes.grammar.spacy_lang_lib import lang_pack
from quizzes.grammar.lang_abr import lang_to_abr

class WordsConnect:
  def __init__(self, lang = 'en'):
      self.lang = lang_to_abr(lang)
      self.nlp = spacy.load(lang_pack[self.lang])

  def words_connections(self, text):
      doc = self.nlp(text)
      nsubjs = []
      for token in doc:
            nsubjs.append([token.head.text, token.text])
      return nsubjs

  def words_nsubj(self, text):
      doc = self.nlp(text)
      nsubjs = []
      for token in doc:
        if token.dep_ == 'nsubj':
            nsubjs.append([token.head.text, token.text])
      return nsubjs

'''
aa = WordsConnect("I'm the king here.", 'english')
#aa = WordsConnect("Я недавно пошла в кино.", 'ru')
doc = aa.words_connections()
for token in doc:
    if token.dep_ == 'nsubj':
        print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_, token.i+1, token.head.i+1))
'''