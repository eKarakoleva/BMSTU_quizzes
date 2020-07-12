import random
import string
import numpy as np
import re

from quizzes.repositories import QuizRepository, CourseRepository, QuestionRepository, AnswerRepository, CourseParticipantsRepository, StudentOpenAnswersRepository
from quizzes.models import Cafedra, User, Course, CourseParticipants, Quiz, Questions, Answers, StudentOpenAnswers

def generate_code(lettersCount = 4, digitsCount = 2):
	sampleStr = ''.join((random.choice(string.ascii_letters) for i in range(lettersCount)))
	sampleStr += ''.join((random.choice(string.digits) for i in range(digitsCount)))
	
	# Convert string to list and shuffle it to mix letters and digits
	sampleList = list(sampleStr)
	random.shuffle(sampleList)
	finalString = ''.join(sampleList)
	return finalString

def check_grades(exelent, verygood, good, bad):
	if exelent > verygood and verygood > good and good > bad:
		return True
	else:
		return False

def construct_quiz(quiz_id):
	quesrtr = QuestionRepository(Questions)
	ar = AnswerRepository(Answers)

	questions = quesrtr.get_by_quiz_id(quiz_id)

	quiz = {}

	for question in questions:
		temp = {}
		temp[question.id] = {}
		temp[question.id]['qname'] = question.name
		temp[question.id]['qtype'] = question.qtype
		temp[question.id]['answers'] = {}

		if question.qtype != 'open':
			answers = ar.get_answer_points_and_name_by_question(question.id)
			for answer in answers:
				temp[question.id]['answers'][answer.id] = {}
				temp[question.id]['answers'][answer.id]['answer'] = answer.name
				temp[question.id]['answers'][answer.id]['points'] = answer.points
		
		quiz.update(temp)
	return quiz

def open_answers_for_check(quiz_id, stud_id):
	quesrtr = QuestionRepository(Questions)
	open_questions = quesrtr.get_open_questions(quiz_id)
	soar = StudentOpenAnswersRepository(StudentOpenAnswers)

	if open_questions:
		for oq in open_questions:
			student_answer = soar.get_stud_open_answer_text(quiz_id, stud_id, oq['id'])
			oq['stud_answer'] = student_answer
	return open_questions

def construct_main(quiz_id):
	quesrtr = QuestionRepository(Questions)
	ar = AnswerRepository(Answers)

	questions = quesrtr.get_id_and_type(quiz_id)

	quiz = {}

	for question in questions:
		temp = {}
		temp[question.id] = {}
		temp[question.id]['qtype'] = question.qtype
		temp[question.id]['answers'] = {}

		if question.qtype != 'open' != 'compare':
			answers = ar.get_answer_points_by_question(question.id)
			for answer in answers:
				temp[question.id]['answers'][answer.id] = answer.points
			
		quiz.update(temp)
	return quiz  

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
	ar = AnswerRepository(Answers)
	answers = ar.get_answer_points_and_name_by_question(question_id)
	for answer in answers:
		teacher_answer, student_answer = prepare_string(str(answer.name), stud_answer)
		distance = levenshtein_ratio_and_distance(teacher_answer, student_answer)
		if(distance == 0):
			return answer.points
	return 0

