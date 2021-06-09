
import os.path
from pathlib import Path
from quizzes.grammar.Tokenizer import Tokenizer
import quizzes.grammarDB.checkerOperations as checkerop
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
        self.ethalon_template = dict()

    def read_ethalon_sents_from_file(self):
        file_path = self.path + "\\" + str(self.lang) + "_ethalons.txt"
        if os.path.isfile(file_path):
            with open(file_path) as f:
                sent_count = 0
                for line in f:
                    ethalon_dict = dict()
                    if sent_count not in ethalon_dict.keys():
                        ethalon_dict[sent_count] = {'ethalons': [], 'check_sents': [], 'expected': {}}
                    lines = line.rstrip()
                    sents_in_line = self.tokenizer.tokenize_sent(lines)
                    for sent in sents_in_line:
                        ethalon_dict[sent_count]['ethalons'].append(sent)
                    sent_count += 1
                    self.ethalon_template.update(ethalon_dict)
        
    def fill_ethalon_template(self, mistake_type):
        file_path = self.path + "\\" + str(self.lang) + "_" + mistake_type + ".txt"
        ethalon_dict = dict()
        if os.path.isfile(file_path):
            ethalon_dict = self.ethalon_template.copy()
            with open(file_path) as fp:
                Lines = fp.readlines()
                sent_count = 0
                for line in Lines:
                    temp = dict()
                    lines = line.rstrip()
                    print("SSS: ", lines)
                    checked_sents_and_results = lines.split("#%#")
                    sents = checked_sents_and_results[0]
                    ethalon_dict[sent_count]['check_sents'].append(sents)
                    expected_res = checked_sents_and_results[1].split("*")
                    for i in range(1, len(expected_res)):
                        sent_res = expected_res[i].split(" ")
                        temp[sent_res[0]] = dict()
                        for j in range(1, len(sent_res)):
                            word_error = sent_res[j].split(":")
                            temp[sent_res[0]][word_error[0]] = {'error': []}
                            errors = word_error[1].split(',')
                            print("SENT: ",sent_count, sents)
                            for error in errors:
                                temp[sent_res[0]][word_error[0]]['error'].append(int(error))
                    ethalon_dict[sent_count]['expected'] = temp
                    sent_count += 1
        return ethalon_dict

    def test_results(self, error_form):
        expected_res = self.fill_ethalon_template(error_form)
        if expected_res:
            print(expected_res)
            
            gc = checkerop.GrammarChecker(self.lang)
            words_counter = 0
            corrected_words = 0
            file_path = self.path + "\\" + str(self.lang) + "_" + error_form +"_res" + ".txt"
            f = open(file_path, "w")
            
    
            for example_count in expected_res:
                #if example_count == 14:
                    #break
                print("EXAMP_COUNT:", example_count)
                gc.ethalon_info_prepare(expected_res[example_count]['ethalons'], test = True)
                gc.prepare_checking_sents(expected_res[example_count]['check_sents'][0])
                corrected_sent= gc.process_mistakes()
                corrected_sent = gc.remove_end_tags_corrected_sents(corrected_sent)
                for sent_count in range(0, len(gc.word_error_struct)):
                    print("SENT_COUNT:", sent_count, gc.word_error_struct)
                    for word_count in range(0, len(gc.word_error_struct[sent_count])):
                        if str(word_count) in expected_res[int(example_count)]['expected'][str(sent_count)].keys():
                            words_counter+=1
                            result =  all(elem in gc.word_error_struct[sent_count][word_count]['error']  for elem in expected_res[example_count]['expected'][str(sent_count)][str(word_count)]['error'])
                            if result:
                                corrected_words += 1
                            else:
                                
                                f.write("ETHALON: " + str(expected_res[int(example_count)]['ethalons']) + "\n")
                                f.write("CHECKING: " + str(expected_res[int(example_count)]['check_sents']) + "\n")
                                f.write("EXAMPLE: " + str(example_count + 1) + " SENT: " + str(sent_count + 1) + " WORD: " + str(word_count) + " " + str(gc.word_error_struct[sent_count][word_count]) + " EXPECTED: " +   str(expected_res[int(example_count)]['expected'][str(sent_count)][str(word_count)]['error']) + "\n\n")
                                print("\n\n\n\nsent count: ", sent_count, expected_res[example_count]['check_sents'])
                                print(result, gc.word_error_struct[sent_count][word_count]['word'] , gc.word_error_struct[sent_count][word_count]['error'], expected_res[example_count]['expected'][str(sent_count)][str(word_count)]['error'])
                                print("AAAA: ", gc.word_error_struct[sent_count][word_count])
                                print("\BBBB: ", expected_res[int(example_count)]['expected'][str(sent_count)][str(word_count)]['error'])

                    #expected_res[example_count]['expected'][sent_count][word_count]['error']
                    
                    #print(gc.word_error_struct[sent_count][word_count]['error'])
                gc.reset()
            f.write("RESULT: " + str(corrected_words) + "/" + str(words_counter) + " = " +str((corrected_words/words_counter) * 100) + "%\n")
            f.close()  
       



'''
{sent: {word: {'error': -6}}
{0: {0: {'error': -6}}
'''