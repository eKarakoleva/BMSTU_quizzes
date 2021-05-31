from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)
from quizzes.forms import TeacherSignUpForm, QuizForm, QuestionForm, AnswerForm, CourseForm, QuizActivateForm, QuizInCodeForm, CourseInCodeForm
from quizzes.models import Cafedra, Course, StudentGrammarAnswers, User, Quiz, Questions, Answers, QuizSolveRecord, CourseParticipants, StudentOpenAnswers, GrammarQuestionSanctions, Languages
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from quizzes.decorators import teacher_required
from django.http import HttpResponse, JsonResponse, Http404

import quizzes.repositories as repo
from django.core import serializers
from django.template.loader import render_to_string

from django.db import connection
#from django.contrib import messages
#from django import forms

from quizzes.helper import check_grades, generate_code, open_answers_for_check, grammar_answers_for_check, construct_quiz_teacher, construct_quiz_student_results, isfloat
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json

import quizzes.grammarDB.checkerOperations as checkerop

class TeacherSignUpView(CreateView):
	model = User
	form_class = TeacherSignUpForm
	template_name = 'registration/signup_form.html'
	success_url = reverse_lazy('login')

	def get_context_data(self, **kwargs):
		kwargs['user_type'] = 'teacher'
		kwargs["queryset"] = Cafedra.objects.filter()
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		user = form.save()
		return redirect('index')


@method_decorator([login_required, teacher_required], name='dispatch')
class CourseListView(ListView,):
	model = Course
	ordering = ('name', )
	context_object_name = 'courses'
	template_name = 'teachers/lists/course_list.html'

	def get_queryset(self):
		course = repo.CourseRepository(Course)
		return course.get_by_user__cafedra_owner(self.request.user)

@method_decorator([login_required, teacher_required], name='dispatch')
class CourseCreateView(CreateView):
	model = Course
	form_class = CourseForm
	template_name = 'teachers/add/course_add.html'
	
	def form_valid(self, form):
		course = form.save(commit=False)
		course.owner = self.request.user
		course.save()
		messages.success(self.request, 'The course was created with success! Go ahead and add some quizzes now.')
		return redirect('/teachers/')

#@method_decorator([login_required], name='dispatch')
@login_required
@teacher_required
def view_course_quizzes(request, pk):
	quiz = repo.QuizRepository(Quiz)
	quizzes = quiz.get_by_user_course(request.user, pk)
	courses = repo.CourseRepository(Course)
	course_name, course_points = courses.get_name_and_points(pk)
	owner_id = courses.get_owner_id(pk)
	if(request.user.id == owner_id):
		return render(request, 'teachers/lists/quiz_list.html', {'quizzes': quizzes, 'course_id': pk, 'course_name': course_name, 'course_points': course_points})
	raise Http404

@method_decorator([login_required, teacher_required], name='dispatch')
class CourseDelete(DeleteView):
	def  get(self, request):
		courseR = repo.CourseRepository(Course)
		cou_id = request.GET.get('id', None)
		owner_id = courseR.get_owner_id(cou_id)
		if request.user.id == owner_id:
			courseR.course_delete(cou_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)

@login_required
@teacher_required
def update_course(request, pk, template_name='teachers/update/update_course.html'):
	course= get_object_or_404(Course, pk=pk)
	courses = repo.CourseRepository(Course)
	owner_id = courses.get_owner_id(pk)

	if request.user.id == owner_id:
		form = CourseForm(request.POST or None, instance=course)
		if form.is_valid():
			points = form.cleaned_data["points"]
			quiz = repo.QuizRepository(Quiz)
			all_quiz_points = quiz.get_all_quiz_points(pk)
			difference = round(points - all_quiz_points, 1)
			if(difference >= 0):
				form.save()
				messages.success(request, 'Course is updated')
			else:
				messages.error(request, 'Course is not updated. Quizzes in the course have more points than new course points', extra_tags='alert')

			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404

@login_required
@teacher_required
def view_course_info(request, pk, template_name='teachers/info/course_info.html'):
	course= get_object_or_404(Course, pk=pk)
	coursesR = repo.CourseRepository(Course)
	owner_id = coursesR.get_owner_id(pk)
	courses = coursesR.get_by_id(pk)
	if request.user.id == owner_id:
		return render(request, template_name, {'id': pk, 'courses': courses})
	raise Http404

@method_decorator([login_required, teacher_required], name='dispatch')
class ActivateDeactivateCourse(UpdateView):
	def  get(self, request):
		courses = repo.CourseRepository(Course)
		course_id = request.GET.get('id', None)
		status = request.GET.get('is_active', None)
		owner_id = courses.get_owner_id(course_id)
		if request.user.id == owner_id:
			if status == 'True':
				courses.update_is_active_and_in_code(course_id, status, generate_code())
			else:
				qr = repo.QuizRepository(Quiz)
				qr.update_all_course_quizzes_status(course_id, status)
				courses.update_is_active(course_id, status)
			data = {
				'activated': True
			}
			return JsonResponse(data)


@login_required
@teacher_required
def quiz_add(request, pk):
	course = get_object_or_404(Course, pk=pk, owner_id=request.user)
	courses = repo.CourseRepository(Course)
	c_points = courses.get_points(pk)
	quizzes = repo.QuizRepository(Quiz)
	all_q_points = quizzes.get_all_quiz_points(pk)
	free_points = c_points - all_q_points
	free_points = round(free_points, 1)

	if request.method == 'POST':
		form = QuizForm(request.POST)
		if form.is_valid():
			quiz = form.save(commit=False)
			quiz.course = course
			quiz.owner = request.user
			max_points = form.cleaned_data["max_points"]

			difference = round(max_points - free_points, 1)
			if(difference <= 0):
				quiz.max_points = round(max_points, 1)
				quiz.save()
				messages.success(request, 'You may now add question/options to the quiz.')
				return redirect('/teachers/course/%d/quizzes'%pk)
			else:
				messages.error(request, 'You put more points than you have left. Available points: %f'%free_points, extra_tags='alert')
	else:
		form = QuizForm()
	return render(request, 'teachers/add/quiz_add.html', {'course': course, 'form': form, 'free_points':free_points })

@method_decorator([login_required, teacher_required], name='dispatch')
class QuizDelete(DeleteView):
	def  get(self, request):
		quizR = repo.QuizRepository(Quiz)		
		quiz_id = request.GET.get('id', None)
		is_active = quizR.is_active(quiz_id)
		owner_id = quizR.get_owner_id(quiz_id)
		if request.user.id == owner_id and not is_active:
			quizR.quiz_delete(quiz_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)

@login_required
@teacher_required
def update_quiz(request, pk, template_name='teachers/update/update_quiz.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizzes = repo.QuizRepository(Quiz)
	owner_id = quizzes.get_owner_id(pk)
	is_active = quizzes.is_active(pk)

	if request.user.id == owner_id and not is_active:
		questions = repo.QuestionRepository(Questions)
		sum_question_points = questions.sum_all_quiz_questions_points(pk)
		cur_quiz_points = quizzes.get_quiz_points(pk)

		form = QuizForm(request.POST or None, instance=quiz)
		if form.is_valid():
			quiz = form.save(commit=False)
			form_points_data = form.cleaned_data["max_points"]
			quiz.max_points = round(form_points_data, 1)
			if_points_changed = round(form_points_data - cur_quiz_points, 1)

			if if_points_changed != 0:
				course_id = quizzes.get_course_id(pk)
				all_q_points = quizzes.get_all_quiz_points(course_id)
				c_points = quizzes.get_course_points(pk)
				free_points = c_points - all_q_points + cur_quiz_points
				free_points = round(free_points, 1)

				if form_points_data > free_points:
					quiz.max_points = cur_quiz_points
					messages.error(request, 'Available course points: %f. '%free_points, extra_tags='alert')
				if sum_question_points > form_points_data:
					quiz.max_points = cur_quiz_points
					messages.error(request, 'Question points in this quiz are: %f. '%sum_question_points, extra_tags='alert')
			quiz.save()
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'sum_questions_points': sum_question_points})
	raise Http404

@login_required
@teacher_required
def view_quiz_info(request, pk, template_name='teachers/info/quiz_info.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizzesR = repo.QuizRepository(Quiz)
	owner_id = quizzesR.get_owner_id(pk)
	quizzes = quizzesR.get_by_id(pk)
	return render(request, template_name, {'id': pk, 'quizzes': quizzes})


@method_decorator([login_required, teacher_required], name='dispatch')
class DeactivateQuiz(UpdateView):
	def  get(self, request):
		quizR = repo.QuizRepository(Quiz)
		questionR = repo.QuestionRepository(Questions)
		quiz_id = request.GET.get('id', None)
		owner_id = quizR.get_owner_id(quiz_id)
		if request.user.id == owner_id:
			quizR.update_is_active(quiz_id, False)
			messages.success(request, 'Success!')
			data = {
				'deactivated': True
			}
			return JsonResponse(data)

@login_required
@teacher_required
def activate_quiz(request, pk, template_name='teachers/activate/activate_quiz.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizR = repo.QuizRepository(Quiz)
	#owner_id = quizR.get_owner_id(pk)
	owner_id = quiz.owner_id
	
	if request.user.id == owner_id:
		is_course_active = quizR.is_course_active(pk)
		form = QuizActivateForm(request.POST or None, instance=quiz)
		if is_course_active:
			questionR = repo.QuestionRepository(Questions)
			is_quiz_done = questionR.is_quiz_done(pk)
			sum_questions_points = questionR.sum_all_quiz_questions_points(pk)
			quiz_points = quizR.get_quiz_points(pk)
			is_active = quizR.is_active(pk)
			
			if form.is_valid():
				quiz = form.save(commit=False)
				check = check_grades(form.cleaned_data["max_points"], form.cleaned_data["good_points"], form.cleaned_data["min_points"])
				if check:
					if(sum_questions_points == quiz_points):
						if is_quiz_done:
							quiz.in_code = generate_code()
							quiz.save()
							quizR.update_is_active(pk, not is_active)
							messages.success(request, 'Success!')
							
						else:
							messages.error(request, 'You have question that dont have enough answers')
					else:
						messages.error(request, 'Sum of quiz queston is not equal quiz points')
					
				else:
					messages.error(request, 'Put points in the right order')
				return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
			return render(request, template_name, {'form':form, 'id': pk})
		else:
			messages.error(request, 'Please activate course first.')
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
	else:
		raise Http404

@login_required
@teacher_required
def view_quiz_questions(request, pk):
	questionsR = repo.QuestionRepository(Questions)
	questions = questionsR.get_by_quiz_id(pk)
	quiz = repo.QuizRepository(Quiz)
	quizzes = quiz.get_by_id(pk)
	course_id = quiz.get_course_id(pk)
	if quizzes:
		owner_id = quizzes[0].owner_id
	else:
		owner_id = 0

	if request.user.id == owner_id:
		return render(request, 'teachers/lists/questions_list.html', {'questions': questions, 'quiz': pk, 'quizzes': quizzes, 'quiz_is_active': quizzes[0].is_active, 'course_id': course_id})
	raise Http404

@login_required
@teacher_required
def view_question_info(request, pk, template_name='teachers/info/question_info.html'):
	#question= get_object_or_404(Questions, pk=pk)
	questionR = repo.QuestionRepository(Questions)
	owner_id = questionR.get_owner_id(pk)
	questions = questionR.get_by_id(pk)
	grammar_points = []
	if questions[0].qtype == 'grammar':
		grammar_points = questionR.get_grammar_points(pk)
	if request.user.id == owner_id:
		return render(request, template_name, {'id': pk, 'questions': questions, 'grammar_points': grammar_points})
	raise Http404

@login_required
@teacher_required
def question_add(request, pk):
	quiz= get_object_or_404(Quiz, pk=pk)
	owner_id = quiz.owner_id
	is_active = quiz.is_active

	if request.user.id == owner_id and not is_active:
		questionR = repo.QuestionRepository(Questions)
		quiz_points = quiz.max_points
		sum_questions_points = questionR.sum_all_quiz_questions_points(pk)

		free_points = quiz_points - sum_questions_points
		free_points = round(free_points, 1)

		if request.method == 'POST':
			can_save = True
			is_grammar = False
			form = QuestionForm(request.POST)
			if form.is_valid():
				question = form.save(commit=False)
				question.quiz_id = pk
				if (form.cleaned_data["qtype"] == 'open'):
					question.done = True 
				cleaned_data_user = form.cleaned_data["points"]
				if free_points >= cleaned_data_user:
					question.points = round(cleaned_data_user, 1) 
					if "spelling-points" in request.POST.keys():
						is_grammar = True
						sp = float(request.POST["spelling-points"])
						gp = float(request.POST["grammar-points"])
						tp = float(request.POST["translate-points"])
						lang = request.POST["lang"]
						langRepo = repo.LanguagesRepository(Languages)
						lang_query = langRepo.get_language(lang)
						if lang_query != -1:
							minus_points = sp + gp + tp
							if minus_points > cleaned_data_user:
								can_save = False
								messages.error(request, 'You cant have spelling and grammar points more that total question points!', extra_tags='alert')
						else:
							can_save = False
					if can_save:
						question.save()
						if is_grammar:
							gsr = repo.GrammarQuestionSanctionsRepository(GrammarQuestionSanctions)
							gsr.add_grammar_sanctions(question.id, sp, gp, tp, lang_query[0].id)
						messages.success(request, 'You may now add answers/options to the question.')
						return redirect('/teachers/course/quiz/%d/questions/'%pk)
				else:
					messages.error(request, 'You put more points than you have left. Available points: %f'%free_points, extra_tags='alert')
		else:
			form = QuestionForm()
		return render(request, 'teachers/add/question_add.html', {'form': form, 'free_points': free_points, 'quiz_id': quiz.id})
	raise Http404

@login_required
@teacher_required
def update_question(request, pk, template_name='teachers/update/update_question.html'):
	question= get_object_or_404(Questions, pk=pk)
	questions = repo.QuestionRepository(Questions)
	owner_id = questions.get_owner_id(pk)
	is_actve = questions.get_quiz_status(pk)

	if request.user.id == owner_id and not is_actve:
		cur_question_points = questions.get_question_points(pk)
		answers = repo.AnswerRepository(Answers)
		sum_answers_points, exist = answers.sum_all_question_answers_points_if_exist(pk)

		form = QuestionForm(request.POST or None, instance=question)
		if form.is_valid():
			update_status = -1
			question = form.save(commit=False)

			form_points_data = form.cleaned_data["points"]
			if_points_changed = round(form_points_data - cur_question_points, 1)

			if if_points_changed != 0:

				same_points = False
				question.points = round(form_points_data, 1)
				quiz_id = questions.get_quiz_id(pk)
				sum_quiz_questions = questions.sum_all_quiz_questions_points(quiz_id)
				quiz_points = questions.get_quiz_points(pk)
				aval_points = quiz_points - sum_quiz_questions + cur_question_points
				aval_points = round(aval_points, 1)

				if (form_points_data > aval_points):
					question.points = cur_question_points
					same_points = True
					messages.error(request, 'Available course points: %f. '%aval_points)
				if (form_points_data < sum_answers_points):
					question.points = cur_question_points
					messages.error(request, 'Answer points in this question are: %f. '%sum_answers_points)
				is_done = questions.get_done_status(pk)
				
				if form_points_data > sum_answers_points and not same_points:
					if is_done == True:
						update_status = 0
						#questions.update_is_done(pk, False)
				else:
					if is_done == False and form_points_data == sum_answers_points:
						update_status = 1
						#questions.update_is_done(pk, True)
			
			update_type = form.cleaned_data["qtype"]
			if update_type == 'open' or update_type == 'compare':
				qtype = questions.get_question_type(pk)
				if qtype != 'open' and qtype != 'compare':
					if not exist:
						update_status = 1
					else:
						question.qtype = qtype
						messages.error(request, 'Can not change type of the question to open or compare. There are answers in this question!')
			question.save()	

			if update_status == 1:
				questions.update_is_done(pk, True)
			else:
				if update_status == 0:
					questions.update_is_done(pk, False)
			
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'sum_answers': sum_answers_points})
	raise Http404

@method_decorator([login_required, teacher_required], name='dispatch')
class QuestionDelete(DeleteView):
	def  get(self, request):
		questionR = repo.QuestionRepository(Questions)
		que_id = request.GET.get('id', None)
		owner_id = questionR.get_owner_id(que_id)
		if request.user.id == owner_id:
			questionR.question_delete(que_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)

@login_required
@teacher_required
def AnswersView(request, qpk):
	form = AnswerForm()

	questions = repo.QuestionRepository(Questions)
	question = questions.get_by_id(qpk)
	owner_id = questions.get_owner_id(qpk)

	if question:
		qtype = question[0].qtype
	else:
		qtype = "NONE"

	grammar_points = []
	if question[0].qtype == 'grammar':
		grammar_points = questions.get_grammar_points(qpk)
		
	if request.user.id == owner_id and qtype != 'open':
		answersR = repo.AnswerRepository(Answers)
		answers = answersR.get_by_id_ordered(qpk)
		quiz_is_active = questions.get_quiz_status(qpk)
		quiz_id = questions.get_quiz_id(qpk)
		return render(request, "teachers/lists/answers_list.html", {"form": form, "answers": answers, "question_id": qpk, "question": question, 'quiz_is_active': quiz_is_active, 'quiz_id': quiz_id, 'qtype': qtype, 'grammar_points': grammar_points})
	raise Http404

@login_required
@teacher_required
def add_answer(request, qpk):
	# request should be ajax and method should be POST.
	if request.is_ajax and request.method == "POST":
		# get the form data
		form = AnswerForm(request.POST)
		# save the data and after fetch the object in instance
		if form.is_valid():

			instance = form.save(commit=False)
			answers = repo.AnswerRepository(Answers)
			sum_answers_points = answers.sum_all_question_answers_points(qpk)
			questions = repo.QuestionRepository(Questions)
			question_type = questions.get_question_type(qpk)

			if question_type != 'grammar':
				question_points = questions.get_question_points(qpk)
				form_points_data = form.cleaned_data["points"]
				instance.points = round(form_points_data, 1)
				free_points = question_points - sum_answers_points
				free_ponts = round(free_points, 1)
				instance.question_id = qpk

				left_points = round(free_points - form_points_data, 1)
				instance.points = round(form_points_data, 1)
				if form_points_data < free_points or left_points == 0.0:
					instance.save()
					messages.success(request, 'Success!')
				else:
					instance.points = 0
					instance.save()
					messages.error(request, 'You put more points than you have left. Available points: %f'%free_points)
				# serialize in new friend object in json
				ser_instance = serializers.serialize('json', [ instance, ])

				if left_points == 0:
					questions.update_is_done(qpk, True)
			else:
				instance.points = 0
				instance.question_id = qpk
				instance.save()
				questions.update_is_done(qpk, True)
				messages.success(request, 'Success!')
				ser_instance = serializers.serialize('json', [ instance, ])


			# send to client side.
			return JsonResponse({"instance": ser_instance}, status=200)
		else:
			# some form errors occured.
			return JsonResponse({"error": form.errors}, status=400)

	# some error occured
	return JsonResponse({"error": ""}, status=400)

@method_decorator([login_required, teacher_required], name='dispatch')
class DeleteAnswer(DeleteView):
	def  get(self, request):
		data = {
			'deleted': False
		}
		answersR = repo.AnswerRepository(Answers)
		ans_id = request.GET.get('id', None)
		quiz_id = answersR.get_quiz_id(ans_id)
		quiz = repo.QuizRepository(Quiz)
		owner_id = quiz.get_owner_id(quiz_id)
		questions = repo.QuestionRepository(Questions)
		question_id = answersR.get_question_id(ans_id)
		question_type = questions.get_question_type(question_id)
		answer_points = answersR.get_answer_points(ans_id)
		is_done = questions.get_done_status(question_id)

		is_deleted = False
		if request.user.id == owner_id:
			answersR.answer_delete(ans_id)
			is_deleted = True
			data = {
				'deleted': True
		}
		if is_deleted:
			if question_type != 'grammar':
				if is_done == True:
					if answer_points != 0:
						questions.update_is_done(question_id, False)
			else:
				answersRepo = repo.AnswerRepository(Answers)
				answers_count = answersRepo.get_answers_count(question_id)
				print(answers_count)
				if is_done == True and answers_count == 0:
					questions.update_is_done(question_id, False)

		return JsonResponse(data)

@login_required
@teacher_required
def update_answer(request, pk, template_name='teachers/update/item_edit_form.html'):
	answer= get_object_or_404(Answers, pk=pk)
	answersR = repo.AnswerRepository(Answers)
	quiz_id = answersR.get_quiz_id(pk)
	quiz = repo.QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(quiz_id)

	if request.user.id == owner_id:
		form = AnswerForm(request.POST or None, instance=answer)

		if form.is_valid():	
			instance = form.save(commit=False)
			form_points_data = form.cleaned_data["points"]
			answer_points = answersR.get_answer_points(pk)

			are_points_changed = round(answer_points - form_points_data, 1)
			if are_points_changed != 0:
				questions = repo.QuestionRepository(Questions)
				question_id = answersR.get_question_id(pk)
				sum_answers_points = answersR.sum_all_question_answers_points(question_id)
				question_points = answersR.get_question_points(question_id)
				answer_points = answersR.get_answer_points(pk)
				free_points = question_points - sum_answers_points + answer_points
				free_points = round(free_points, 1)

				instance.points =  round(form_points_data, 1)
				is_done = questions.get_done_status(question_id)

				difference = round(free_points - form_points_data, 1)
				
				if difference >= 0:
					if(difference == 0):
						if is_done == False: 
							questions.update_is_done(question_id, True)
					else:
						if is_done == True:
							questions.update_is_done(question_id, False)
					messages.success(request, 'Success!')
				else:
					instance.points = answer_points
					messages.error(request, 'You put more points than you have left. Available points: %f'%free_points)
			instance.save()
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404


@login_required
@teacher_required
def view_quiz_for_check(request, pk):
	quiz = repo.QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(pk)
	if request.user.id == owner_id:
		quiz_name = quiz.get_name(pk)
		qsr = repo.QuizSolveRecordRepository(QuizSolveRecord)
		quizzes = qsr.get_quizzes_and_students(pk, False)
		course_id  = quiz.get_course_id(pk)
		return render(request, 'teachers/lists/check_quiz_list.html', {'quizzes': quizzes, 'course_id': course_id, 'quiz_name': quiz_name})
	raise Http404


@csrf_exempt
@login_required
@teacher_required
def get_answers_for_check(request, pk, spk):
	quiz = repo.QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(pk)
	course_id = quiz.get_course_id(pk)
	cpr = repo.CourseParticipantsRepository(CourseParticipants)
	is_participant = cpr.is_user_participant(spk, course_id)

	if request.user.id == owner_id and is_participant:
		quiz_name = quiz.get_name(pk)
		answers = open_answers_for_check(pk, spk)
		answers_grammar = grammar_answers_for_check(pk, spk)
		print(answers_grammar)
		return render(request, 'teachers/check_quiz/check_quiz.html', {'answers': answers, 'answers_grammar':answers_grammar, 'quiz_id': pk, 'student_id': spk, 'quiz_name': quiz_name})
	raise Http404

@csrf_exempt
@login_required
@teacher_required
def save_checked_answers(request, pk, spk):
	quiz = repo.QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(pk)
	course_id = quiz.get_course_id(pk)
	cpr = repo.CourseParticipantsRepository(CourseParticipants)
	is_participant = cpr.is_user_participant(spk, course_id)

	if request.user.id == owner_id and is_participant:
		questionRepo = repo.QuestionRepository(Questions)
		new_points = request.POST['data']
		new_points = json.loads(new_points)

		quesrtr = repo.QuestionRepository(Questions)
		open_questions = quesrtr.get_open_questions_id_points(pk)
		soar = repo.StudentOpenAnswersRepository(StudentOpenAnswers)
		qsrr = repo.QuizSolveRecordRepository(QuizSolveRecord)
		sgar = repo.StudentGrammarAnswersRepository(StudentGrammarAnswers)
		solve_info_id = qsrr.get_solve_info_id(pk, spk)

		#new_points[i]['name'] - id
		#new_points[i]['value'] - points
		sum_points = 0
		for i in range(1, len(new_points)):
			for j in range(0, len(open_questions)):
				question_id = int(new_points[i]['name'])
				print("QUESTION_ID: ",question_id)
				if question_id == open_questions[j]['id']:
					points = round(float(new_points[i]['value']), 1)
					open_question_points = float(open_questions[j]['points'])
					if points <= open_question_points:
						soar.update_answer_points(solve_info_id, question_id, points)
						sum_points += points
					else:
						soar.update_answer_points(solve_info_id, question_id, open_question_points)
						sum_points += open_question_points					
					break
				else:
					quiz_id_points = questionRepo.get_quiz_id_and_type_points(question_id)
					if len(quiz_id_points) != 0:
						if quiz_id_points['qtype'] == 'grammar':
							if isfloat(new_points[i]['value']):
								points = round(float(new_points[i]['value']), 1)
								if points <= quiz_id_points['points']:
									sgar.update_answer_points(solve_info_id, question_id, points)
									sum_points += points
								else:
									sgar.update_answer_points(solve_info_id, question_id, quiz_id_points['points'])
									sum_points += quiz_id_points['points']	
							else:
								sgar.update_answer_corrected(solve_info_id, question_id, new_points[i]['value'])

				
		student_points = qsrr.get_points(solve_info_id)
		qsrr.update_quiz_points_and_status(solve_info_id, student_points + sum_points, True)
		return JsonResponse({
			'success': True,
			'url': reverse('teachers:view_quiz_for_check', kwargs={'pk': pk}), #, args=[{'courses': courses}]
			})
	raise Http404

@login_required
@teacher_required
def quiz_update_in_code(request, pk, template_name='teachers/update/update_in_code.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizzes = repo.QuizRepository(Quiz)
	owner_id = quizzes.get_owner_id(pk)

	if request.user.id == owner_id:

		form = QuizInCodeForm(request.POST or None, instance=quiz)
		if form.is_valid():
			quiz = form.save(commit=False)
			if len(form.cleaned_data["in_code"]) <= 6:
				quiz.save()
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404

@login_required
@teacher_required
def grammar_checker(request):
	return render(request, 'teachers/grammer_checker.html', {})

@login_required
@teacher_required
def course_update_in_code(request, pk, template_name='teachers/update/course_update_in_code.html'):
	course= get_object_or_404(Course, pk=pk)
	cr = repo.CourseRepository(Course)
	owner_id = cr.get_owner_id(pk)

	if request.user.id == owner_id:

		form = CourseInCodeForm(request.POST or None, instance=course)
		if form.is_valid():
			course = form.save(commit=False)
			if len(form.cleaned_data["in_code"]) <= 6:
				course.save()
			return HttpResponse(render_to_string('teachers/update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404

@login_required
@teacher_required
def view_students_quiz_grades(request, pk):
	quiz_ch = get_object_or_404(Quiz, pk=pk)
	quiz = repo.QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(pk)
	if request.user.id == owner_id:
		qsr = repo.QuizSolveRecordRepository(QuizSolveRecord)
		quizzes = qsr.get_quizzes_and_students(pk, True)
		course_id  = quiz.get_course_id(pk)
		points = quiz.get_point_schedule(pk)
		max_points = 0
		min_points = 0
		good_points = 0

		if points:
			max_points = points[0]['max_points']
			min_points = points[0]['min_points']
			good_points = points[0]['good_points']

		return render(request, 'teachers/lists/students_grade_list.html', {'quizzes': quizzes, 'course_id': course_id, 'min_points': min_points, 'good_points': good_points, 'max_points': max_points})
	raise Http404


@login_required
@teacher_required
def quiz_preview(request, pk):
	qr = repo.QuizRepository(Quiz)
	owner_id = qr.get_owner_id(pk)
	if request.user.id == owner_id:
		test = construct_quiz_teacher(pk)
		quiz_name =qr.get_name(pk)
		course_id = qr.get_course_id(pk)
		return render(request, 'teachers/view/quiz_preview.html', {'tests': test, 'quiz_name': quiz_name, 'course_id': course_id})
	else:
		raise Http404

def student_quiz_view(request, pk, spk):
	qr = repo.QuizRepository(Quiz)
	owner_id = qr.get_owner_id(pk)
	if request.user.id == owner_id:
		cpr = repo.CourseParticipantsRepository(CourseParticipants)

		is_in_joined_courses = cpr.is_quiz_in_joined_courses(pk, spk)
		if not is_in_joined_courses:
			raise Http404
	    
		test = construct_quiz_student_results(pk, spk)
		quiz_name =qr.get_name(pk)
		return render(request, 'teachers/view/student_quiz_view.html', {'tests': test, 'quiz_name': quiz_name, 'quiz_id': pk, 'role': 'teacher'})
	raise Http404

def course_participants_list(request, pk):	
	cr = repo.CourseRepository(Course)
	owner_id = cr.get_owner_id(pk)
	if request.user.id == owner_id:
		cpr = repo.CourseParticipantsRepository(CourseParticipants)
		participants = cpr.get_course_participants(pk)
		course_name = cr.get_name(pk)
		return render(request, 'teachers/lists/quiz_participants.html', {'participants': participants, 'course_name': course_name})
	raise Http404

@teacher_required
@login_required
def test_grammar(request, qpk):
	gqsr = repo.GrammarQuestionSanctionsRepository(GrammarQuestionSanctions)
	lang_id = gqsr.get_language(qpk)
	if lang_id != -1:
		
		langRepo = repo.LanguagesRepository(Languages)
		lang = langRepo.get_abr_by_id(lang_id)
		print("LANG: ", lang)
		#aa = checkerop.levenshtein_ratio_and_distance('going', 'go', ratio_calc = True)
		#print("RATIO: ", aa)
		sents_to_check = request.GET.get('sents', None)
		print(sents_to_check)
		ethalonts = checkerop.get_etalons(qpk)
		error_struct_result, error_codes, corrected_sent = checkerop.process_checking(ethalonts, sents_to_check, lang)

	data = {
		'error_result': error_struct_result,
		'error_codes': error_codes,
		'corrected_sent': corrected_sent
	}
	return JsonResponse(data)