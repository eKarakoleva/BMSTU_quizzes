from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)
from quizzes.forms import StudentSignUpForm, CourseForm, QuestionForm, AnswerForm
from quizzes.models import Cafedra, User, Course, CourseParticipants, Quiz, Questions, QuizSolveRecord, StudentAnswers,StudentOpenAnswers
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from quizzes.decorators import student_required

import quizzes.repositories as repo
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.forms.formsets import formset_factory
import quizzes.helper as helper
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
import datetime
from django.utils import timezone

class StudentSignUpView(CreateView):
	model = User
	form_class = StudentSignUpForm
	template_name = 'registration/signup_form.html'
	success_url = reverse_lazy('login')

	def get_context_data(self, **kwargs):
		kwargs['user_type'] = 'student'
		kwargs["queryset"] = Cafedra.objects.filter()
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		user = form.save()
		return redirect('index')


@login_required
@student_required
def view_all_not_joined_couses(request):
	course = repo.CourseRepository(Course)
	courses = course.get_not_join_courses(request.user.id)
	return render(request, 'students/lists/course_list.html', {'courses': courses})

@login_required
@student_required
def join_course(request, pk, template_name='students/join_course.html'):
	course= get_object_or_404(Course, pk=pk)
	courses = repo.CourseRepository(Course)
	if request.method == 'POST':
		code = request.POST.get('code')
		in_code = courses.get_course_code(pk)
		if in_code == code:
			cp = repo.CourseParticipantsRepository(CourseParticipants)
			cp.join_course(request.user.id,pk)
			messages.success(request, 'Welcome to the course')
		else:
			messages.error(request, 'Please enter the right varification code.')

		return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
	else:
		return render(request, template_name, {'id': pk})

@login_required
@student_required
def join_quiz(request, pk, template_name='students/join_quiz.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	qr = repo.QuizRepository(Quiz)
	if request.method == 'POST':
		code = request.POST.get('code')
		in_code = qr.get_quiz_code(pk)
		if in_code == code:
			qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
			is_started = qsrr.check_if_started(pk, request.user.id)
			if(not is_started):
				qsrr.start_quiz(pk, request.user.id)

			return redirect('students:take_quiz', pk=pk)
			messages.success(request, 'Welcome to the course')
		else:
			messages.error(request, 'Please enter the right varification code.')
			return redirect('students:take_quiz_confirm', pk=pk)
	else:
		return render(request, template_name, {'id': pk})



@login_required
@student_required
def view_all_joined_couses(request):
	cp = repo.CourseParticipantsRepository(CourseParticipants)
	courses = cp.get_joined_courses(request.user.id)
	return render(request, 'students/lists/joined_courses.html', {'courses': courses})

@login_required
@student_required
def take_quiz_confirm(request, pk):
	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	is_started = qsrr.check_if_started(pk, request.user.id)
	qr = repo.QuizRepository(Quiz)
	quiz = qr.get_by_id(pk)
	course_id = qr.get_course_id(pk) 

	cpr = repo.CourseParticipantsRepository(CourseParticipants)
	is_in_joined_courses = cpr.is_quiz_in_joined_courses(pk, request.user.id)
	if not is_in_joined_courses:
		raise Http404

	minutes_left = 0
	if quiz:
		if is_started:
			timer = quiz[0].timer_minutes
			if timer != 0:
				start_time = qsrr.get_start_time(pk, request.user.id)
				end_time = start_time + datetime.timedelta(minutes = timer)

				now = timezone.now()
				now = timezone.localtime(now)
				time_delta = (end_time - now)

				minutes_left = time_delta.seconds / 60
		else:
			minutes_left = quiz[0].timer_minutes
	return render(request, 'students/confirm/take_quiz_confirm.html', {'quiz': quiz, 'course_id': course_id, 'minutes_left': round(minutes_left), 'is_started': is_started})


@login_required
@student_required
def take_quiz(request, pk):
	qr = repo.QuizRepository(Quiz)
	test = helper.construct_quiz(pk)
	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	cpr = repo.CourseParticipantsRepository(CourseParticipants)

	is_in_joined_courses = cpr.is_quiz_in_joined_courses(pk, request.user.id)
	if not is_in_joined_courses:
		raise Http404

	is_submitted = qsrr.if_quiz_is_submitted(pk, request.user.id)
	if is_submitted:
		raise Http404

	is_started = qsrr.check_if_started(pk, request.user.id)
	if(not is_started):
		raise Http404

	timer = qr.get_quiz_timer(pk)
	start_time = qsrr.get_start_time(pk, request.user.id)
	time = start_time + datetime.timedelta(minutes = timer)

	now = timezone.now()
	now = timezone.localtime(now)
	time_delta = (time - now)

	time_delta = time_delta.seconds / 60
	quiz_name =qr.get_name(pk)

	if time_delta > timer and timer != 0:
		raise Http404 #TODO page time is end

	return render(request, 'students/quiz_solve.html', {'tests': test, 'quiz_id': pk, 'timer': timer, 'minutes_left': time_delta, 'quiz_name': quiz_name})

def view_course_active_quizzes(request, pk):
	cpr = repo.CourseParticipantsRepository(CourseParticipants)
	is_in_joined_courses = cpr.is_quiz_in_joined_courses(pk, request.user.id)
	if not is_in_joined_courses:
		raise Http404
		
	quiz = repo.QuizRepository(Quiz)
	quizzes = quiz.get_active_quizzes_student_info(pk, request.user.id)
	if not quizzes:
		raise Http404
	else:
		course_name = quizzes[0].course

	return render(request, 'students/lists/quiz_list.html', {'quizzes': quizzes, 'course_name': course_name})

@csrf_exempt
@login_required
@student_required
def finish_test(request, pk):
	student_answers = request.POST['data']
	student_answers = json.loads(student_answers)
	quiz_data = helper.construct_main(pk)
	is_fully_checked = True
	points = 0
	qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
	solve_info_id = qsrr.get_solve_info_id(pk, request.user.id)
	solve_info_id = int(solve_info_id)
	sar = repo.StudentAnswersRepository(StudentAnswers)
	soar = repo.StudentOpenAnswersRepository(StudentOpenAnswers)
	for i in range(1, len(student_answers)):
		if i != 0:
			#name = question_id
			#value = answer_id or answer to open question
			key = int(student_answers[i]['name'])
			#check if question_id belongs to quiz
			if key in quiz_data.keys():
				if quiz_data[key]['qtype'] != 'open' and quiz_data[key]['qtype'] != 'compare':
					#check if answer_id belongs to question
					answer_id = int(student_answers[i]['value'])
					if answer_id in quiz_data[key]['answers'].keys():
						points += float(quiz_data[key]['answers'][answer_id])
						#create record 
						sar.save_answer(solve_info_id, key, answer_id)
				else:
					answer = student_answers[i]['value']
					if quiz_data[key]['qtype'] == 'open':
						is_fully_checked = False
						soar.save_answer(solve_info_id, key, answer, 0)
					if(len(answer)):
						if quiz_data[key]['qtype'] == 'compare':
							points_compare = helper.check_student_compare_answer(key, str(answer))
							points += points_compare
							#save answer + compare algorithm = points
							soar.save_answer(solve_info_id, key, answer, points_compare)
	qsrr.finish_quiz(pk, request.user.id, points, is_fully_checked)
	qr = repo.QuizRepository(Quiz)
	course_id = qr.get_course_id(pk)
	return JsonResponse({
		'success': True,
		'url': reverse('students:view_course_active_quizzes', kwargs={'pk': course_id}), #, args=[{'courses': courses}]
		})

@login_required
@student_required
def student_view_quiz_info(request, pk, template_name='students/quiz_info.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizzesR = repo.QuizRepository(Quiz)
	owner_id = quizzesR.get_owner_id(pk)
	quizzes = quizzesR.get_by_id(pk)
	return render(request, template_name, {'id': pk, 'quizzes': quizzes})


def graded_quiz_view(request, pk):
	qr = repo.QuizRepository(Quiz)

	cpr = repo.CourseParticipantsRepository(CourseParticipants)
	is_in_joined_courses = cpr.is_quiz_in_joined_courses(pk, request.user.id)
	if not is_in_joined_courses:
		raise Http404

	test = helper.construct_quiz_student_results(pk, request.user.id)
	quiz_name =qr.get_name(pk)
	course_id = qr.get_course_id(pk)
	return render(request, 'teachers/view/student_quiz_view.html', {'tests': test, 'quiz_name': quiz_name, 'quiz_id': pk, 'course_id': course_id})
