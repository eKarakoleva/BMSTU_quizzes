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

	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	solve_info_id = qsrr.get_solve_info_id(quiz_id, stud_id)
	print("QUIZ: ", solve_info_id )
	if grammar_questions:
		for gq in grammar_questions:
			student_answer = sgar.get_stud_grammar_answer_info(solve_info_id, gq['id'])
			if not student_answer:
				gq['exist'] = False
			else:
				gq['checked_result'] = json.loads(student_answer[0]['check_result'])
				#gq['points'] = gq[0]['points']
				gq['exist'] = True
				gq['stud_answer'] = student_answer[0]['answer']
				gq['corrected_sent'] = student_answer[0]['corrected_sent']
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


def check_student_grammar_answer(question_id, stud_answer):
	gqsr = repo.GrammarQuestionSanctionsRepository(GrammarQuestionSanctions)
	lang_id = gqsr.get_language(question_id)
	error_struct_result = ""
	if lang_id != -1:
		langRepo = repo.LanguagesRepository(Languages)
		lang = langRepo.get_abr_by_id(lang_id)
		print("LANG: ", lang)
		print(stud_answer)
		ethalonts = checkerop.get_etalons(question_id)
		error_struct_result, _ , corrected_sent = checkerop.process_checking(ethalonts, stud_answer, lang)

		error_struct_result = json.dumps(error_struct_result)
	return error_struct_result, corrected_sent


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False