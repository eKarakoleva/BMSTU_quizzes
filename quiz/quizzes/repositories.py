#from quizzes.models import Cafedra, Course, User, Quiz, Question, Answers

class QuizRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_user_course(self, user_id, course_id):
		return self.model.objects.filter(owner_id=user_id, course_id = course_id)

	def get_by_user_course__course(self, user_id, course_id):
		return self.model.objects.filter(owner_id = user_id, course_id = course_id).select_related('course')

	def get_by_id(self, q_id):
			return self.model.objects.filter(id = q_id)

	def get_owner_id(self, q_id):
		return self.model.objects.only('owner_id').get(id=q_id).owner_id

	def quiz_delete(self, quizpk):
		return self.model.objects.get(id=quizpk).delete()

class CourseRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_user__cafedra_owner(self, user_id):
		return self.model.objects.filter(owner_id = user_id).select_related('course_cafedra').select_related('owner')

	def get_by_id(self, quiz_id):
		 self.model.objects.get(id = quiz_id).order_by('-id').reverse()

	def get_owner_id(self, c_id):
		return self.model.objects.only('owner_id').get(id=c_id).owner_id

	def course_delete(self, cpk):
		return self.model.objects.get(id=cpk).delete()


class QuestionRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id(self, qpk):
		return self.model.objects.filter(id = qpk)

	def get_by_quiz_id(self, quiz_id):
			return self.model.objects.filter(quiz_id = quiz_id).order_by('-id').reverse()

	def get_owner_id(self, question_id):
		return self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__owner_id')[0]['quiz__owner_id']

	def question_delete(self, qpk):
		return self.model.objects.get(id=qpk).delete()



class AnswerRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id_ordered(self, qpk):
		return self.model.objects.filter(question_id  = qpk).order_by('-points').reverse()

	def answer_delete(self, apk):
		return self.model.objects.get(id=apk).delete()

	def get_owner_id(self, aid):
		#return self.model.objects.filter(question_id=question_id).select_related('question').select_related('quiz').values('quiz__owner_id')[0]['quiz__owner_id']
		quer = self.model.objects.raw('SELECT qqz.id, qqz.owner_id \
								FROM test.quizzes_answers as qa \
								LEFT JOIN test.quizzes_questions as qq \
								ON qa.question_id = qq.id \
								LEFT JOIN test.quizzes_quiz as qqz \
								ON qq.quiz_id = qqz.id \
								where qa.id = %s LIMIT 1', [aid])
		for p in quer:
			return p.owner_id