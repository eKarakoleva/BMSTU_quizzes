from nltk.tokenize import word_tokenize, sent_tokenize
from string import punctuation
from quizzes.grammar.lang_abr import abr_to_lang

END_TOKEN = '__sent__'
my_punctuation = punctuation.replace("'", "").replace("-", "").replace("_", "")

class Tokenizer:
  def __init__(self, lang="english"):
    self.lang = abr_to_lang(lang)

    self.my_punctuation = my_punctuation

  def remove_punctuation(self, text):
    return text.translate(str.maketrans('', '', self.my_punctuation))

  def make_downcase(self, text):
    return text.lower()

  def prepare_not_self_text(self, text):
      text = self.remove_punctuation(text)
      text = self.make_downcase(text)

      return text

  def tokenize_word(self, text, prepare = True):
    if prepare:
      text = self.remove_punctuation(text)
      #text = self.make_downcase(text)
    return word_tokenize(text, language=self.lang)

  def tokenize_sent(self, text):
    st = sent_tokenize(text, language=self.lang)
    sentences = []
    for s in st:
      sentences.append(self.remove_punctuation(s))
    return sentences

  def tokenize_with_punctuatuion(self, text):
    st = sent_tokenize(self.make_downcase(text), language=self.lang)
    return st  

  def word_by_sent(self, sents):
    sent_res = []
    for s in sents:
      sent_res.append(self.tokenize_word(s))
    return sent_res

  def generate_ngrams(self, tokens_sent, n, prepare = False, end_tag = False):
    #tokens_sent = tok.tokenize_sent()
    ngrams_res = []
    for ts in tokens_sent:
      n_words = len(self.tokenize_word(ts, prepare))
      if prepare:
        ts = self.prepare_not_self_text(ts)
      if n_words < n:
        if end_tag:
          ts_temp = END_TOKEN + " " + ts + " " + END_TOKEN
          ts = ts_temp
          print("\n\n\nTS: ", ts)
          #ts += " " + END_TOKEN
          ngrams_res.append([ts])
          #ngrams_res.append([])
      else:
        if end_tag:
          #ts += " " + END_TOKEN
          ts_temp = END_TOKEN + " " + ts + " " + END_TOKEN
          #ts += END_TOKEN + " " + ts + " " + END_TOKEN
          ts = ts_temp
          print("\n\n\nTS: ", ts)

        tokens = [token for token in self.tokenize_word(ts, prepare) if token != ""]
        ngrams = zip(*[tokens[i:] for i in range(n)])
        ngrams_res.append([" ".join(ngram) for ngram in ngrams])
    return ngrams_res

  def generate_different_ngrams(self, tokens_, n, unique_ngrams = dict(), end_tag = True):
    for i in range(len(tokens_)):
      tokens = tokens_[i]
      if end_tag and END_TOKEN not in tokens:
        tokens.append(END_TOKEN)
        tokens.insert(0, END_TOKEN)
      ngrams = zip(*[tokens[i:] for i in range(n)])
      ngram_comb =[" ".join(ngram) for ngram in ngrams]
      for nc in ngram_comb:
        if nc not in unique_ngrams:
          unique_ngrams[nc] = 1
        else:
          unique_ngrams[nc] += 1
    return unique_ngrams
    

'''
#tok = Tokenizer("I don`t have much fun here! But it's fun there")
tok = Tokenizer("Я - к.т.н. Сижу на диван-кровати. Но там не очень удобно.", "en")
tok.prepare_text()
sents = tok.tokenize_sent()
print("sents: ", sents)
print(tok.word_by_sent(sents))
print(tok.generate_ngrams(sents, 3))
'''