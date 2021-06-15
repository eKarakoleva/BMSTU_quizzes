import random
import string
import numpy as np
import re
import random
import json
import ast
import quizzes.repositories as repo
from quizzes.models import Questions, Answers, StudentOpenAnswers, QuizSolveRecord, StudentAnswers, GrammarQuestionSanctions,StudentGrammarAnswers, Languages
import quizzes.grammarDB.checkerOperations as checkerop

def generate_code(lettersCount = 4, digitsCount = 2):
	sampleStr = ''.join((random.choice(string.ascii_letters) for i in range(lettersCount)))
	sampleStr += ''.join((random.choice(string.digits) for i in range(digitsCount)))
	
	# Convert string to list and shuffle it to mix letters and digits
	sampleList = list(sampleStr)
	random.shuffle(sampleList)
	finalString = ''.join(sampleList)
	return finalString

def check_grades(exelent, good, bad):
	if exelent > good and good > bad:
		return True
	else:
		return False

def construct_quiz(quiz_id):
	quesrtr = repo.QuestionRepository(Questions)
	ar = repo.AnswerRepository(Answers)

	questions = quesrtr.get_by_quiz_id(quiz_id)
	#questions = list(questions)
	#random.shuffle(questions)
	quiz = {}

	for question in questions:
		temp = {}
		temp[question.id] = {}
		temp[question.id]['qname'] = question.name
		temp[question.id]['qtype'] = question.qtype
		temp[question.id]['answers'] = {}

		if question.qtype != 'open':
			answers = ar.get_answer_points_and_name_by_question(question.id)
			count_true = 0
			answers = list(answers)
			random.shuffle(answers)
			for answer in answers:
				temp[question.id]['answers'][answer.id] = {}
				temp[question.id]['answers'][answer.id]['answer'] = answer.name
				temp[question.id]['answers'][answer.id]['points'] = answer.points
				if answer.correct == True:
					count_true += 1
			temp[question.id]['cor_ans'] = count_true
		quiz.update(temp)				
	return quiz

def construct_quiz_teacher(quiz_id):
	quesrtr = repo.QuestionRepository(Questions)
	ar = repo.AnswerRepository(Answers)

	questions = quesrtr.get_by_quiz_id(quiz_id)

	quiz = {}

	for question in questions:
		temp = {}
		temp[question.id] = {}
		temp[question.id]['qname'] = question.name
		temp[question.id]['qtype'] = question.qtype
		temp[question.id]['points'] = question.points
		temp[question.id]['description'] = question.description
		temp[question.id]['answers'] = {}

		if question.qtype != 'open':
			answers = ar.get_answer_points_and_name_by_question(question.id)
			for answer in answers:
				temp[question.id]['answers'][answer.id] = {}
				temp[question.id]['answers'][answer.id]['answer'] = answer.name
				temp[question.id]['answers'][answer.id]['points'] = answer.points
				temp[question.id]['answers'][answer.id]['correct'] = answer.correct
		quiz.update(temp)
	return quiz

def construct_main(quiz_id):
	quesrtr = repo.QuestionRepository(Questions)
	ar = repo.AnswerRepository(Answers)

	questions = quesrtr.get_id_and_type(quiz_id)

	quiz = {}

	for question in questions:
		temp = {}
		temp[question.id] = {}
		temp[question.id]['qtype'] = question.qtype
		temp[question.id]['answers'] = {}

		if question.qtype == 'multiple' or  question.qtype == 'single':
			answers = ar.get_answer_points_by_question(question.id)
			for answer in answers:
				temp[question.id]['answers'][answer.id] = answer.points
			
		quiz.update(temp)
	return quiz  
	
def construct_quiz_student_results(quiz_id, student_id):

	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	solve_info_id = qsrr.get_solve_info_id(quiz_id, student_id)

	if solve_info_id != 0:
		sar = repo.StudentAnswersRepository(StudentAnswers)
		stud_answers = sar.get_student_answers(solve_info_id)
		quesrtr = repo.QuestionRepository(Questions)
		ar = repo.AnswerRepository(Answers)
		answers_id = [ sub['answer_id'] for sub in stud_answers ] 
		
		questions = quesrtr.get_by_quiz_id(quiz_id)

		soar = repo.StudentOpenAnswersRepository(StudentOpenAnswers)
		sgar = repo.StudentGrammarAnswersRepository(StudentGrammarAnswers)
		quiz = {}

		for question in questions:
			temp = {}
			temp[question.id] = {}
			temp[question.id]['qname'] = question.name
			temp[question.id]['qtype'] = question.qtype
			temp[question.id]['points'] = question.points
			temp[question.id]['description'] = question.description
			temp[question.id]['answers'] = {}


			if question.qtype != 'open' and question.qtype != 'compare' and question.qtype != 'grammar':
				answers = ar.get_answer_points_and_name_by_question(question.id)
				for answer in answers:
					temp[question.id]['answers'][answer.id] = {}
					temp[question.id]['answers'][answer.id]['answer'] = answer.name
					temp[question.id]['answers'][answer.id]['points'] = answer.points
					temp[question.id]['answers'][answer.id]['correct'] = answer.correct
					if answer.id in answers_id:
						temp[question.id]['answers'][answer.id]['is_answer'] = True
					else:
						temp[question.id]['answers'][answer.id]['is_answer'] = False
			else:
				if question.qtype != 'grammar':
					open_student_answers = soar.get_student_answers(solve_info_id, question.id)
					temp[question.id]['answers']['answer'] = ""
					temp[question.id]['answers']['points'] = 0
					if open_student_answers != -1:
						temp[question.id]['answers']['answer'] = open_student_answers['answer']
						temp[question.id]['answers']['points'] = open_student_answers['points']
				else:
					open_student_answers = sgar.get_student_answers(solve_info_id, question.id)
					temp[question.id]['answers']['answer'] = ""
					temp[question.id]['answers']['points'] = 0
					if open_student_answers != -1:
						temp[question.id]['answers']['answer'] = open_student_answers['answer']
						temp[question.id]['answers']['points'] = open_student_answers['points']
						temp[question.id]['answers']['result'] =  json.loads(open_student_answers['check_result'])
						temp[question.id]['answers']['corrected_sents'] =  open_student_answers['corrected_sent']
								

			quiz.update(temp)
		return quiz
	else:
		return -1

def open_answers_for_check(quiz_id, stud_id):
	quesrtr = repo.QuestionRepository(Questions)
	open_questions = quesrtr.get_open_questions(quiz_id)
	soar = repo.StudentOpenAnswersRepository(StudentOpenAnswers)

	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	solve_info_id = qsrr.get_solve_info_id(quiz_id, stud_id)
	if open_questions:
		for oq in open_questions:
			student_answer = soar.get_stud_open_answer_text(solve_info_id, oq['id'])
			if not student_answer:
				oq['exist'] = False
			else:
				oq['exist'] = True
				oq['stud_answer'] = student_answer[0]['answer']
	return open_questions

def grammar_answers_for_check(quiz_id, stud_id):
	quesrtr = repo.QuestionRepository(Questions)
	grammar_questions = quesrtr.get_grammar_questions(quiz_id)
	sgar = repo.StudentGrammarAnswersRepository(StudentGrammarAnswers)
	gqsr = repo.GrammarQuestionSanctionsRepository(GrammarQuestionSanctions)
	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	solve_info_id = qsrr.get_solve_info_id(quiz_id, stud_id)
	if grammar_questions:
		for gq in grammar_questions:
			student_answer = sgar.get_stud_grammar_answer_info(solve_info_id, gq['id'])
			if not student_answer:
				gq['exist'] = False
			else:
				
				sanctions = gqsr.form_error_sanction_dict_error_names(gq['id'])
				ethalonts = checkerop.get_etalons(gq['id'])
				
				ethalon = ""
				for eth in ethalonts:
					ethalon += eth['name'] + ". "
				gq['checked_result'] = json.loads(student_answer[0]['check_result'])
				#gq['points'] = gq[0]['points']
				gq['exist'] = True
				gq['stud_answer'] = student_answer[0]['answer']
				gq['corrected_sent'] = student_answer[0]['corrected_sent']
				gq['suggested_points'] = student_answer[0]['points']
				gq['sanctions'] = sanctions
				gq['ethalons'] = ethalon
				print(ethalon)
	return grammar_questions

def prepare_string(str1, str2):
	#remove special charaters from string
	str1 = re.sub (r'[^A-Za-z0-9]+', ' ', str1)
	str2 = re.sub (r'[^A-Za-z0-9]+', ' ', str2)
	#remove extra spaces
	str1 = re.sub("\s\s+" , " ", str1)
	str2 = re.sub("\s\s+" , " ", str2)

	return str1, str2

def levenshtein_ratio_and_distance(s, t, ratio_calc = False):
	""" levenshtein_ratio_and_distance:
		Calculates levenshtein distance between two strings.
		If ratio_calc = True, the function computes the
		levenshtein distance ratio of similarity between two strings
		For all i and j, distance[i,j] will contain the Levenshtein
		distance between the first i characters of s and the
		first j characters of t
	"""
	# Initialize matrix of zeros
	rows = len(s)+1
	cols = len(t)+1
	distance = np.zeros((rows,cols),dtype = int)

	# Populate matrix of zeros with the indeces of each character of both strings
	for i in range(1, rows):
		for k in range(1,cols):
			distance[i][0] = i
			distance[0][k] = k

	# Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
	for col in range(1, cols):
		for row in range(1, rows):
			if s[row-1] == t[col-1]:
				cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
			else:
				# In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
				# the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
				if ratio_calc == True:
					cost = 2
				else:
					cost = 1
			distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
								 distance[row][col-1] + 1,          # Cost of insertions
								 distance[row-1][col-1] + cost)     # Cost of substitutions
	if ratio_calc == True:
		# Computation of the Levenshtein Distance Ratio
		Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
		return Ratio
	else:
		return distance[row][col]


def check_student_compare_answer(question_id, stud_answer):
	ar = repo.AnswerRepository(Answers)
	answers = ar.get_answer_points_and_name_by_question(question_id)
	for answer in answers:
		teacher_answer, student_answer = prepare_string(str(answer.name), stud_answer)
		distance = levenshtein_ratio_and_distance(teacher_answer, student_answer)
		if(distance == 0):
			return answer.points
	return 0


def check_student_grammar_answer(question_id, stud_answer, question_sanctions, grammarChecker):
	error_struct_result = ""
	ethalonts = checkerop.get_etalons(question_id)
	error_struct_result, _ , corrected_sent = grammarChecker.process_checking(ethalonts, stud_answer)
	points_sanctions = calculate_grammar_question_points(error_struct_result, question_sanctions)
	qr = repo.QuestionRepository(Questions)
	#print("\n\n\nSANCTIONS: ", points_sanctions)
	question_points = qr.get_question_points(question_id)
	points_for_question = question_points - points_sanctions
	if points_for_question < 0:
		points_for_question = 0
	points_for_question = round(points_for_question, 2)
	error_struct_result = json.dumps(error_struct_result)
	#print("nSANCTIONS", corrected_sent)
	return error_struct_result, corrected_sent, points_for_question

def calculate_grammar_question_points(struct, question_sanctions):
	mistakes_count  = dict()
	points_sanctions = 0
	for key in checkerop.error_explain.keys():
		if key not in mistakes_count.keys():
			mistakes_count[key] = 0

	for sent_i in range(len(struct)):
		for word_i in range(len(struct[sent_i])):
			for error in struct[sent_i][word_i]['error']:
				if error in mistakes_count.keys():
					mistakes_count[error] += 1
					if checkerop.WORD_FORM_MISTAKE in struct[sent_i][word_i]['error'] and checkerop.NOT_IN_ETHALON in struct[sent_i][word_i]['error']:
						mistakes_count[checkerop.NOT_IN_ETHALON] -= 1

	if mistakes_count[checkerop.NOT_IN_ETHALON] < 0:
		mistakes_count[checkerop.NOT_IN_ETHALON] = 2*mistakes_count[checkerop.WORD_FORM_MISTAKE]
	double_errors = [checkerop.WRONG_ORDER, checkerop.TRANSLATION_MISTAKE,checkerop.NOT_IN_ETHALON,checkerop.GRAMMAR_MISTAKE]
	for key in mistakes_count.keys():
		if key in double_errors:
			if mistakes_count[key] > 1:
				if mistakes_count[key] % 2 == 0:
					mistakes_count[key] /= 2
				else:
					mistakes_count[key] -= 1
		points_sanctions += mistakes_count[key] * question_sanctions[key]
		#print(mistakes_count)
	return points_sanctions



def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False


def get_lang_options_for_question(lrepo, question_id):
	gsr = repo.GrammarQuestionSanctionsRepository(GrammarQuestionSanctions)
	lang_id_quest = gsr.get_language(question_id)
	all_lang = lrepo.get_all()
	lang_struct = dict()
	for l in all_lang:
		if l.abr not in lang_struct.keys():
			lang_struct[l.abr] = False
			if l.id == lang_id_quest:
				lang_struct[l.abr] = True

	return lang_struct

