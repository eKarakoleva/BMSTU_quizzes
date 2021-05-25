import spacy
from quizzes.grammar.spacy_lang_lib import lang_pack
from quizzes.grammar.lang_abr import lang_to_abr

class WordsConnect:
  def __init__(self, lang = 'en'):
      self.lang = lang_to_abr(lang)
      self.nlp = spacy.load(lang_pack[self.lang], disable=["attribute_ruler", "morphologizer", "lemmatizer"])

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

  def words_nsubj_aux(self, text):
      doc = self.nlp(text)
      nsubjs = []
      auxes = []
      for token in doc:
        if token.dep_ == 'nsubj':
            nsubjs.append([token.head.text, token.text])
        else:
            if token.dep_ == 'aux':
                auxes.append([token.head.text, token.text])
      return nsubjs, auxes

  def words_nsubj_with_position(self, text):
      doc = self.nlp(text)
      nsubjs = []
      for token in doc:
        if token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass':
            nsubjs.append([token.head.text, token.text, token.head.i, token.i])
      return nsubjs


  def words_nsubj_aux_with_position(self, text):
      doc = self.nlp(text)
      nsubjs = []
      auxs = []
      for token in doc:
        if token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass':
            nsubjs.append([token.head.text, token.text, token.head.i, token.i])
        else:
            if token.dep_ == 'aux' or token.dep_ == 'auxpass':
                
                auxs.append([token.head.text, token.text, token.head.i, token.i])
      return nsubjs, auxs
'''
        for nsubj in nsubjcts:
            nsubj_connections.update({nsubj[0]: nsubj[1]})
aa = WordsConnect("I'm the king here.", 'english')
#aa = WordsConnect("Я недавно пошла в кино.", 'ru')
doc = aa.words_connections()
for token in doc:
    if token.dep_ == 'nsubj':
        print("{2}({3}-{6}, {0}-{5})".format(token.text, token.tag_, token.dep_, token.head.text, token.head.tag_, token.i+1, token.head.i+1))
'''