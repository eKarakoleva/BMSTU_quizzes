from django.db.models import Sum

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

	def get_all_quiz_points(self, course_id):
		points = self.model.objects.filter(course_id=course_id).aggregate(Sum('max_points'))['max_points__sum']
		if(not points):
			points = 0
		return points

	def get_course_id(self, quizpk):
		return self.model.objects.only('course_id').get(id=quizpk).course_id

	def get_quiz_points(self, quizpk):
		return self.model.objects.only('max_points').get(id=quizpk).max_points

	def get_course_points(self, quiz_id):
		return self.model.objects.filter(id=quiz_id).select_related('course').values('course__points')[0]['course__points']

	def update_is_active(self, quiz_id, status):
		return self.model.objects.filter(id=quiz_id).update(is_active=status)

	def is_active(self, quizpk):
		return self.model.objects.only('is_active').get(id=quizpk).is_active



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

	def get_points(self, c_id):
		return self.model.objects.only('points').get(id=c_id).points

	def update_is_active(self, course_id, status):
		return self.model.objects.filter(id=course_id).update(is_active=status)


class QuestionRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id(self, qpk):
		return self.model.objects.filter(id = qpk)

	def get_by_quiz_id(self, quiz_id):
			return self.model.objects.filter(quiz_id = quiz_id).order_by('-id').reverse()


	def get_owner_id(self, question_id):
		return self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__owner_id')[0]['quiz__owner_id']

	def get_quiz_status(self, question_id):
		return self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__is_active')[0]['quiz__is_active']

	def question_delete(self, qpk):
		return self.model.objects.get(id=qpk).delete()

	def sum_all_quiz_questions_points(self, quiz_id):
		points = self.model.objects.filter(quiz_id=quiz_id).aggregate(Sum('points'))['points__sum']
		if(not points):
			points = 0
		return points

	def get_quiz_id(self, question_id):
		return self.model.objects.only('quiz_id').get(id=question_id).quiz_id

	def get_quiz_points(self, question_id):
		return self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__max_points')[0]['quiz__max_points']

	def get_question_points(self, question_id):
		return self.model.objects.only('points').get(id=question_id).points

	def get_question_type(self, question_id):
		return self.model.objects.only('qtype').get(id=question_id).qtype

	def update_is_done(self, question_id, status):
		return self.model.objects.filter(id=question_id).update(done=status)

	def get_done_status(self, question_id):
		return self.model.objects.only('done').get(id=question_id).done

	def is_quiz_done(self, quiz_id):
		dones = self.model.objects.filter(quiz_id=quiz_id, done = False).values('done').distinct()
		if dones.exists():
			dones = False
		else:
			dones = True
		return dones




class AnswerRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id_ordered(self, qpk):
		return self.model.objects.filter(question_id  = qpk).order_by('-points').reverse()

	def answer_delete(self, apk):
		return self.model.objects.get(id=apk).delete()

	def get_quiz_id(self, aid):
		return self.model.objects.filter(id=aid).select_related('question').values('question__quiz_id')[0]['question__quiz_id']

	def sum_all_question_answers_points(self, question_id):
		points = self.model.objects.filter(question_id=question_id).aggregate(Sum('points'))['points__sum']
		if(not points):
			points = 0
		return points

	#only for update methods
	def get_question_points(self, question_id):
		points = self.model.objects.filter(question_id=question_id).select_related('question').values('question__points')
		if(not points):
			points = 0
		else:
			points = points[0]['question__points']
		return points

	def get_answer_points(self, answer_id):
		return self.model.objects.only('points').get(id=answer_id).points

	def get_question_id(self, answer_id):
		return self.model.objects.filter(id=answer_id).select_related('question').values('question__id')[0]['question__id']