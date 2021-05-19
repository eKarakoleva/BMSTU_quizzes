from django.db.models import Sum
from quizzes.models import CourseParticipants, User, QuizSolveRecord, Quiz, QuizSolveRecord, GrammarQuestionSanctions
from django.utils import timezone
import datetime

class UserRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id(self, user_id):
		return self.model.objects.filter(id = user_id).select_related('cafedra')

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
		oid = self.model.objects.filter(id = q_id).values('owner_id')
		if not oid:
			oid = 0
		else:
			oid = oid[0]['owner_id']
		return oid

	def get_name(self, quiz_id):
		return self.model.objects.only('name').get(id=quiz_id).name

	def quiz_delete(self, quizpk):
		return self.model.objects.get(id=quizpk).delete()

	def get_all_quiz_points(self, course_id):
		points = self.model.objects.filter(course_id=course_id).aggregate(Sum('max_points'))['max_points__sum']
		if(not points):
			points = 0
		return points

	def get_course_id(self, quizpk):
		cid= self.model.objects.filter(id=quizpk).values('course_id')
		if not cid:
			cid = 0
		else:
			cid = cid[0]['course_id']
		return cid

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

		if all_course_quizzes:
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
		
	def get_point_schedule(self, quizpk):
		return self.model.objects.filter(id=quizpk).values('max_points', 'min_points', 'good_points')

	def get_quiz_timer(self, quiz_id):
		timer = self.model.objects.filter(id=quiz_id).values('timer_minutes')
		if not timer:
			timer = 0
		else:
			timer = timer[0]['timer_minutes']
		return timer

	def update_all_course_quizzes_status(self, course_id, status):
		return self.model.objects.filter(course_id=course_id).update(is_active=status)

	def is_course_active(self, quiz_id):
		return self.model.objects.filter(id=quiz_id).select_related('course').values('course__is_active')[0]['course__is_active']


	def get_quiz_code(self, quiz_id):
		return self.model.objects.only('in_code').get(id=quiz_id).in_code

class CourseRepository(object):
	def __init__(self, model):
		self.model = model

	def get_name(self, course_id):
		name = self.model.objects.filter(id = course_id).values('name')
		if not name:
			name = "NONE"
		else:
			name = name[0]['name']
		return name

	def get_name_and_points(self, course_id):
		name_points = self.model.objects.filter(id = course_id).values('name', 'points')
		name = "NONE"
		points = 0
		if name_points:
			name = name_points[0]['name']
			points = name_points[0]['points']
		return name, points

	def get_all_active(self):
		return self.model.objects.filter(is_active=True)

	def get_by_user__cafedra_owner(self, user_id):
		return self.model.objects.filter(owner_id = user_id).select_related('course_cafedra').select_related('owner')

	def get_by_id(self, course_id):
		 return self.model.objects.filter(id = course_id)

	def get_owner_id(self, c_id):
		oid = self.model.objects.filter(id = c_id).values('owner_id')
		if not oid:
			oid = 0
		else:
			oid = oid[0]['owner_id']
		return oid

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
	
	def update_is_active(self, course_id, status):
		return self.model.objects.filter(id=course_id).update(is_active=status)	

	def is_active(self, course_id):
		return self.model.objects.only('is_active').get(id=course_id).is_active


class QuestionRepository(object):
	def __init__(self, model):
		self.model = model

	def get_by_id(self, qpk):
		return self.model.objects.filter(id = qpk)

	def get_grammar_points(self, qpk):
		return GrammarQuestionSanctions.objects.filter(question_id = qpk)

	def get_by_quiz_id(self, quiz_id):
		return self.model.objects.filter(quiz_id = quiz_id).order_by('-id').reverse()

	def get_id_and_type(self, quiz_id):
		return self.model.objects.filter(quiz_id = quiz_id).only("id", "qtype").order_by('-id').reverse()

	def get_owner_id(self, question_id):
		owner_id = self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__owner_id')
		if owner_id:
			owner_id = owner_id[0]['quiz__owner_id']
		else:
			owner_id = 0
		return owner_id

	def get_quiz_status(self, question_id):
		status = self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__is_active')
		if status:
			status = status[0]['quiz__is_active']
		else:
			status = 0
		return status

	def question_delete(self, qpk):
		return self.model.objects.get(id=qpk).delete()

	def sum_all_quiz_questions_points(self, quiz_id):
		points = self.model.objects.filter(quiz_id=quiz_id).aggregate(Sum('points'))['points__sum']
		if(not points):
			points = 0
		return points

	def get_quiz_id(self, question_id):
		qid = self.model.objects.filter(id=question_id).values('quiz_id')
		if qid.exists():
			qid = qid[0]['quiz_id']
		else:
			qid = 0
		return qid

	def get_quiz_points(self, question_id):
		max_points = self.model.objects.filter(id=question_id).select_related('quiz').values('quiz__max_points')
		if max_points:
			max_points = max_points[0]['quiz__max_points']
		else:
			max_points = 0
		return max_points

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

	def get_open_questions_id_points(self, quiz_id):
		ids = self.model.objects.filter(quiz_id=quiz_id, qtype = 'open').values('id', 'points')
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

	def sum_all_question_answers_points_if_exist(self, question_id):
		points = self.model.objects.filter(question_id=question_id).aggregate(Sum('points'))['points__sum']
		exist = True
		if(not points):
			points = 0
			exist = False
		return points, exist

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
		owner = User.objects.filter(is_teacher=True).values('id','first_name', 'last_name')

		courses = list(courses)
		owners = list(owner)

		for course in courses:
			for owner in owners:
				if course.course.owner_id == owner['id']:
					course.course.owner_ln = owner['last_name']
					course.course.owner_fn = owner['first_name']
					break

		return courses

	def is_quiz_in_joined_active_courses(self, quiz_id ,user_id):
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

	def is_quiz_in_joined_courses(self, quiz_id ,user_id):
		course_id = Quiz.objects.filter(id=quiz_id).values('course_id')

		if course_id:
			joined = self.model.objects.filter(user_id=user_id, course_id = course_id[0]['course_id']).values('id')
			if not joined:
				joined = False
			else:
				joined = True
		else:
			joined = False
		
		return joined


	def is_user_participant(self, user_id, course_id):
		is_participant = self.model.objects.filter(user_id = user_id, course_id = course_id).values('id')
		if not is_participant:
			is_participant = False
		else:
			is_participant = True
		return is_participant

	def get_course_participants(self, course_id):
		participants = self.model.objects.filter(course_id = course_id).select_related('user').values('user__id', 'join_date')

		if participants:
			for participant in participants:
				ur = UserRepository(User)
				user = ur.get_by_id(participant['user__id'])
				
				if user:

					participant['fname'] = user[0].first_name
					participant['lname'] = user[0].last_name
					participant['surname'] = user[0].surname
					participant['cafedra'] = user[0].cafedra

		return participants

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
		solve_id = self.model.objects.filter(quiz_id=quiz_id, student_id=student_id).values('id')
		if(not solve_id):
			solve_id = 0
		else:
			solve_id = solve_id[0]['id']
		return solve_id

	def finish_quiz(self, quiz_id, student_id, points, is_fully_checked):
		#return self.model.objects.filter(quiz_id = quiz_id, student_id = student_id).update(time_end = time_end, points= points, is_fully_checked = is_fully_checked)
		quiz_solve = self.model.objects.get(quiz_id = quiz_id, student_id = student_id)
		quiz_solve.time_end = datetime.datetime.now()
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

	def get_quizzes_and_students(self, quiz_id, is_fully_checked):
		quizzes = self.model.objects.filter(quiz_id=quiz_id, is_fully_checked=is_fully_checked)

		if quizzes.exists():
			for quiz in quizzes:
				student = User.objects.filter(id = quiz.student_id).select_related('cafedra')
				student = list(student)
				if student:
					quiz.stud_id =  student[0].id
					quiz.stud_fname = student[0].first_name
					quiz.stud_surname = student[0].surname
					quiz.stud_lname = student[0].last_name
					quiz.stud_cefedra = student[0].cafedra.name

		return quizzes

	def update_quiz_points_and_status(self, id, points, status):
		if id > 0:
			quiz_solve = self.model.objects.get(id = id)
			quiz_solve.points = points
			quiz_solve.is_fully_checked = status
			quiz_solve.save()

	def get_points(self, id):
		points = self.model.objects.only('points').get(id = id).points
		if(not points):
			points = 0
		return points

	def get_start_time(self, quiz_id, student_id):
		#now_plus_10 = now + datetime.timedelta(minutes = 120)
		#raise Exception({now_plus_10.strftime("%b %d %Y %H:%M:%S")})

		time = self.model.objects.filter(quiz_id = quiz_id, student_id = student_id).values('time_start').distinct()
		if not time.exists():
			time = 0
		else:
			time = timezone.localtime(time[0]['time_start'])
		return time

	def get_end_time(self, quiz_id, student_id):
		#now_plus_10 = now + datetime.timedelta(minutes = 120)
		#raise Exception({now_plus_10.strftime("%b %d %Y %H:%M:%S")})

		time = self.model.objects.filter(quiz_id = quiz_id, student_id = student_id).values('time_end').distinct()
		if not time.exists():
			time = 0
		else:
			time = timezone.localtime(time[0]['time_start'])
		return time

class StudentAnswersRepository(object):
	def __init__(self, model):
		self.model = model

	def save_answer(self, solve_info, question_id, answer_id):
		return self.model.objects.create(
				solve_info_id= solve_info, 
				question_id = question_id, 
				answer_id = answer_id)

	def get_student_answers(self, solve_id):
		answer =  self.model.objects.filter(solve_info_id = solve_id).values('answer_id')
		return answer

class StudentOpenAnswersRepository(object):
	def __init__(self, model):
		self.model = model

	def save_answer(self, solve_info, question_id, answer, points):
		return self.model.objects.create(
				solve_info_id= solve_info,
				question_id = question_id, 
				answer = answer, 
				points = points)

	def get_stud_open_answer_text(self, solve_info_id, question_id):

		if solve_info_id > 0:
			answer =  self.model.objects.filter(solve_info_id = solve_info_id, question_id = question_id).values('answer')
			return answer

	def update_answer_points(self,solve_info_id, question_id, quiz_id, student_id, points):

		if solve_info_id > 0:
			quiz_solve = self.model.objects.get(solve_info_id = solve_info_id, question_id = question_id)
			quiz_solve.points = points
			quiz_solve.save()

	def get_student_answers(self, solve_id, question_id):
		answer =  self.model.objects.filter(solve_info_id = solve_id, question_id = question_id).values('answer', 'points')
		if answer:
			answer = answer[0]
		else:
			answer = -1
		return answer


class LanguagesRepository(object):
	def __init__(self, model):
		self.model = model

	def get_language(self, abr):
		lang = self.model.objects.filter(abr = abr)
		if not lang:
			lang = -1
		return lang

	def get_all(self):
		return self.model.objects.all()

	def add_lang(self, lang, abr):
		return self.model.objects.create(name = lang, abr = abr)

	def get_name_by_abr(self, abr):
		name = self.model.objects.filter(abr = abr).values('name')
		if not name:
			name = -1
		else:
			name = name[0]['name']
		return name

	def get_abr_by_name(self, name):
		abr = self.model.objects.filter(name = name).values('abr')
		if not abr:
			abr = -1
		else:
			abr = abr[0]['abr']
		return abr

	def get_id_by_abr(self, abr):
		id_lang = self.model.objects.filter(abr = abr).values('id')
		if not id_lang:
			id_lang = -1
		else:
			id_lang = id_lang[0]['id']
		return id_lang

	def get_abr_by_id(self, id):
		lang_abr = self.model.objects.filter(id = id).values('abr')
		if not lang_abr:
			lang_abr = -1
		else:
			lang_abr = lang_abr[0]['abr']
		return lang_abr


	def get_record_by_abr(self, abr):
		id_lang = self.model.objects.filter(abr = abr)
		if not id_lang:
			id_lang = -1
		return id_lang
	
	def is_empty(self):
		is_em = False
		res = self.model.objects.all()[:3]
		if len(res) == 0:
			is_em = True
		return is_em

class LearnSetsRepository(object):
	def __init__(self, model):
		self.model = model

	def add_set(self, s_name, language):
		return self.model.objects.create(set_name= s_name, lang_id = language)

	def get_all(self):
		return self.model.objects.all()

	def get_set(self, s_name, language):
		return self.model.objects.filter(set_name= s_name, lang_id = language)

	def is_empty(self):
		is_em = False
		res = self.model.objects.all()[:3]
		if len(res) == 0:
			is_em = True
		return is_em

	def is_lang(self, language):
		is_em = False
		res = self.model.objects.filter(lang_id = language)[:3]
		if len(res) == 0:
			is_em = True
		return is_em

class TagsetRepository(object):
	def __init__(self, model):
		self.model = model

	def add_tag(self, tag_name, lang):
		return self.model.objects.create(tag= tag_name, lang_id = lang)

	def get_tag_id(self, name):
		tag_id = self.model.objects.filter(tag = name).values('id')
		if not tag_id:
			tag_id = -1
		else:
			tag_id = tag_id[0]['id']
		return tag_id

	def get_tag(self, name):
		tag_id = self.model.objects.filter(tag = name)
		if not tag_id:
			tag_id = -1
		return tag_id
	
	def is_empty(self, lang_id):
		is_em = False
		res = self.model.objects.filter(lang_id = lang_id)[:3]
		if len(res) == 0:
			is_em = True
		return is_em


class BiGrammsRepository(object):
	def __init__(self, model):
		self.model = model

	def add_tag_combination(self, tag1_id, tag2_id, comb_count, lang_id, lrn_set):
		return self.model.objects.create(tag1= tag1_id,
										tag2 = tag2_id,
										freq = comb_count,
										lang_id = lang_id,
										learn_set_id = lrn_set)

	def get_combination(self, tag1, tag2):
		tag_comb = self.model.objects.filter(tag1_id = tag1, tag2_id = tag2)
		if not tag_comb:
			tag_comb = -1
		return tag_comb

	def is_empty(self):
		is_em = False
		res = self.model.objects.all()[:3]
		if len(res) == 0:
			is_em = True
		return is_em

	def update_combination_freq(self, rec_id, freq):
		exists = self.model.objects.filter(id=rec_id)
		if len(exists) != 0:
			return self.model.objects.filter(id=exists[0].id).update(freq=int(exists[0].freq) + int(freq))
		else:
			return []

class TriGrammsRepository(object):
	def __init__(self, model):
		self.model = model

	def add_tag_combination(self, tag1_id, tag2_id, tag3_id, comb_count, lang_id, lrn_set):
		return self.model.objects.create(tag1= tag1_id,
										tag2 = tag2_id,
										tag3 = tag3_id,
										freq = comb_count,
										lang_id = lang_id,
										learn_set_id = lrn_set)

	def is_empty(self):
		is_em = False
		res = self.model.objects.all()[:3]
		if len(res) == 0:
			is_em = True
		return is_em

	def get_combination(self, tag1, tag2, tag3):
		tag_comb = self.model.objects.filter(tag1_id = tag1, tag2_id = tag2, tag3_id = tag3)
		if not tag_comb:
			tag_comb = -1
		return tag_comb

	def update_combination_freq(self, rec_id, freq):
		exists = self.model.objects.filter(id=rec_id)
		if len(exists) != 0:
			return self.model.objects.filter(id=exists[0].id).update(freq=int(exists[0].freq) + int(freq))
		else:
			return []


class GrammarQuestionSanctionsRepository(object):
	def __init__(self, model):
		self.model = model

	def add_grammar_sanctions(self, quest_id, spelling, grammar, translate, lang):
		return self.model.objects.create(question_id = quest_id, 
										spelling_points = spelling,
										grammar_points = grammar,
										translate_points = translate,
										lang_id = lang)
	def get_info(self, quest_id):
		qginfo = self.model.objects.filter(question_id = quest_id)
		if not qginfo:
			qginfo = -1
		return qginfo

	def get_language(self, quest_id):
		lang_id = self.model.objects.filter(question_id = quest_id).values('lang_id')
		if not lang_id:
			lang_id = -1
		else:
			lang_id = lang_id[0]['lang_id']
		return lang_id