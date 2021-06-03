
import os.path
from pathlib import Path
from quizzes.grammar.Tokenizer import Tokenizer
'''
en_data = {
    {'ethalons': ['I had just left for school when I saw the postman and he gave it to me.'],
    'check_sents': '',
    'expected' :  {}
    },
    {'ethalons': ['The last time I spoke to you, you talked about giving it up.'],
    'check_sents': '',
    'expected' :  {}
    },
} 
'''
class TestMethod:
    def __init__(self, lang):
        self.lang = lang
        self.ethalon_sents = []
        self.BASE_DIR = Path(__file__).resolve(strict=True).parents[1] 
        self.path = str(self.BASE_DIR) + "\\grammar\\test_data"
        self.tokenizer = Tokenizer(lang = lang)
        self.ethalon_template = []

    def read_ethalon_sents_from_file(self):
        file_path = self.path + "\\" + str(self.lang) + "_ethalons.txt"
        if os.path.isfile(file_path):
            with open(file_path) as f:
                for line in f:
                    ethalon_dict = {'ethalons': [], 'check_sents': [], 'expexted': {}}
                    lines = line.rstrip()
                    sents_in_line = self.tokenizer.tokenize_sent(lines)
                    for sent in sents_in_line:
                        ethalon_dict['ethalons'].append(sent)
                    self.ethalon_template.append(ethalon_dict)
            print(self.ethalon_template)