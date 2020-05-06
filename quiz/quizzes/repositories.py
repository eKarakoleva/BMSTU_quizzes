from quizzes.models import Cafedra, Course, User, Quiz


class QuizRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_user_course(self, user_id, course_id):
		return self.model.objects.filter(owner_id=user_id, course_id = course_id)

	def get_by_user_course__course(self, user_id, course_id):
		return self.model.objects.filter(owner_id = user_id, course_id = course_id).select_related('course')

	def get_by_id(self, q_id):
			return self.model.objects.filter(id = q_id)

class CourseRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_user__cafedra_owner(self, user_id):
		return self.model.objects.filter(owner_id = user_id).select_related('course_cafedra').select_related('owner')

	def get_by_id(self, quiz_id):
		 self.model.objects.get(id = quiz_id)


class QuestionRepository(object):
	def __init__(self, model):
		self.model = model

