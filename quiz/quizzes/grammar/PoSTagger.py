import treetaggerwrapper
from quizzes.grammar.lang_abr import lang_to_abr
from pathlib import Path

class PoSTagger:
  def __init__(self, lang = 'en'):
    self.lang = lang_to_abr(lang)
    self.BASE_DIR = Path(__file__).resolve(strict=True).parents[1]
    self.path = str(self.BASE_DIR) + "\\TreeTagger"
    self.tagger = treetaggerwrapper.TreeTagger(TAGLANG = self.lang, TAGDIR = self.path)

  def tag(self, text):
    return self.tagger.tag_text(text)

'''
pos = PoSTagger("I do not have much fun here. But its fun there.", 'english')
#pos = PoSTagger("Я недавно пошла в кино.", "russian")
tags = pos.tag()
for i in tags:
    a = i.split(" ")
    #print(a[0].split()[1])
    print(a)
'''