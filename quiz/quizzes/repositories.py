from django.db.models import Sum
from quizzes.models import CourseParticipants, User, QuizSolveRecord, Quiz, QuizSolveRecord
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

	def get_active_quizzes(self, course_id):
		return self.model.objects.filter(course_id = course_id, is_active=True).select_related('course')

	def get_active_quizzes_student_info(self, course_id, student_id):
		quiz_student_info = QuizSolveRecord.objects.filter(student_id=student_id)
		all_course_quizzes = self.model.objects.filter(course_id = course_id, is_active=True).select_related('course')

		for quiz in all_course_quizzes:
			quiz.sis_fully_checked = None
			quiz.spoints = 0
			quiz.is_started = False
			for qsi in quiz_student_info:
				if quiz.id == qsi.quiz_id:
					quiz.spoints = qsi.points
					quiz.sis_fully_checked = qsi.is_fully_checked
					quiz.is_started = True
					#quiz.student.time_end = qsi.time_end
		return all_course_quizzes
		

class CourseRepository(object):
	def __init__(self, model):
		self.model = model

	def get_all_active(self):
		return self.model.objects.filter(is_active=True)

	def get_by_user__cafedra_owner(self, user_id):
		return self.model.objects.filter(owner_id = user_id).select_related('course_cafedra').select_related('owner')

	def get_by_id(self, course_id):
		 return self.model.objects.filter(id = course_id)

	def get_owner_id(self, c_id):
		return self.model.objects.only('owner_id').get(id=c_id).owner_id

	def course_delete(self, cpk):
		return self.model.objects.get(id=cpk).delete()

	def get_points(self, c_id):
		return self.model.objects.only('points').get(id=c_id).points

	def update_is_active(self, course_id, status):
		return self.model.objects.filter(id=course_id).update(is_active=status)

	def update_is_active_and_in_code(self, course_id, status, code):
		return self.model.objects.filter(id=course_id).update(is_active=status, in_code=code)

	def get_course_code(self, course_id):
		return self.model.objects.only('in_code').get(id=course_id).in_code

	def get_not_join_courses(self, user_id):
		all_mine = CourseParticipants.objects.filter(user_id = user_id).values_list('course_id')
		all_active = self.model.objects.filter(is_active = True).exclude(id__in=all_mine)
		return all_active
		


class QuestionRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id(self, qpk):
		return self.model.objects.filter(id = qpk)

	def get_by_quiz_id(self, quiz_id):
		return self.model.objects.filter(quiz_id = quiz_id).order_by('-id').reverse()

	def get_id_and_type(self, quiz_id):
		return self.model.objects.filter(quiz_id = quiz_id).only("id", "qtype").order_by('-id').reverse()


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

	def get_open_questions(self, quiz_id):
		ids = self.model.objects.filter(quiz_id=quiz_id, qtype = 'open').values('id', 'points', 'name')
		return ids

class AnswerRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id_ordered(self, qpk):
		return self.model.objects.filter(question_id  = qpk).order_by('-points').reverse()

	def get_answer_points_by_question(self, qpk):
		return self.model.objects.filter(question_id  = qpk).only("id", "points").order_by('-points').reverse()

	def get_answer_points_and_name_by_question(self, qpk):
		return self.model.objects.filter(question_id  = qpk).only("id", "points", "name").order_by('-points').reverse()

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


class CourseParticipantsRepository(object):
	def __init__(self, model):
		self.model = model

	def join_course(self, user_id, course_id):
		return self.model.objects.create(user_id=user_id, course_id = course_id)

	def get_joined_courses(self, user_id):
		courses = self.model.objects.filter(user_id=user_id).select_related('course').filter(course__is_active = True)
		owner_id = User.objects.filter(is_teacher=True).values('id','first_name', 'last_name')

		courses = list(courses)
		owners = list(owner_id)

		for course in courses:
			for owner in owners:
				if course.course.id == owner['id']:
					course.course.owner_ln = owner['last_name']
					course.course.owner_fn = owner['first_name']
					break
		return courses

	def is_quiz_in_joined_courses(self, quiz_id ,user_id):
		course_id = Quiz.objects.filter(id=quiz_id, is_active = True).values('course_id')

		if course_id:
			joined = self.model.objects.filter(user_id=user_id, course_id = course_id[0]['course_id']).values('id')
			if not joined:
				joined = False
			else:
				joined = True
		else:
			joined = False
		
		return joined

class QuizSolveRecordRepository(object):
	def __init__(self, model):
		self.model = model

	def start_quiz(self, quiz_id, student_id):
		return self.model.objects.create(quiz_id=quiz_id, student_id = student_id)

	def check_if_started(self, quiz_id, student_id):
		result = self.model.objects.filter(quiz_id=quiz_id, student_id=student_id)
		ret = True
		if(not result):
			ret = False
		return ret

	def get_solve_info_id(self, quiz_id, student_id):
		solve_id = self.model.objects.only('id').get(quiz_id=quiz_id, student_id=student_id).id
		if(not solve_id):
			solve_id = 0
		return solve_id

	def finish_quiz(self, quiz_id, student_id, points, is_fully_checked):
		#return self.model.objects.filter(quiz_id = quiz_id, student_id = student_id).update(time_end = time_end, points= points, is_fully_checked = is_fully_checked)
		quiz_solve = self.model.objects.get(quiz_id = quiz_id, student_id = student_id)
		quiz_solve.points = points
		quiz_solve.is_fully_checked = is_fully_checked
		quiz_solve.save()

	def if_quiz_is_submitted(self, quiz_id, student_id):
		is_submitted =  self.model.objects.filter(quiz_id=quiz_id, student_id=student_id).values('is_fully_checked')

		if(not is_submitted):
			is_submitted = False
		else:
			is_submitted = is_submitted[0]['is_fully_checked']
			if is_submitted != None:
				is_submitted = True
			else:
				is_submitted = False

		return is_submitted

	def get_quizzes_for_check(self, quiz_id):
		quizzes = self.model.objects.filter(quiz_id=quiz_id, is_fully_checked=False)

		if quizzes.exists():
			for quiz in quizzes:
				student = User.objects.filter(id = quiz.student_id).select_related('cafedra')
				student = list(student)
				if student:
					quiz.stud_id =  student[0].id
					quiz.stud_fname = student[0].first_name
					quiz.stud_lname = student[0].last_name
					quiz.stud_cefedra = student[0].cafedra.name
		return quizzes

class StudentAnswersRepository(object):
	def __init__(self, model):
		self.model = model

	def save_answer(self, solve_info, question_id, answer_id):
		return self.model.objects.create(
				solve_info_id= solve_info, 
				question_id = question_id, 
				answer_id = answer_id)	

class StudentOpenAnswersRepository(object):
	def __init__(self, model):
		self.model = model

	def save_answer(self, solve_info, question_id, answer, points):
		return self.model.objects.create(
				solve_info_id= solve_info,
				question_id = question_id, 
				answer = answer, 
				points = points)

	def get_stud_open_answer_text(self, quiz_id, student_id, question_id):
		qsrr = QuizSolveRecordRepository(QuizSolveRecord)
		solve_info_id = qsrr.get_solve_info_id(quiz_id, student_id)
		answer =  self.model.objects.filter(solve_info_id = solve_info_id, question_id = question_id).values('answer')

		if not answer:
			answer = []
		else:
			answer = answer[0]['answer']
		return answer
