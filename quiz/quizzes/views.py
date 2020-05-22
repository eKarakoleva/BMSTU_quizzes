from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)
from quizzes.forms import TeacherSignUpForm, QuizForm, QuestionForm, AnswerForm, CourseForm
from quizzes.models import Cafedra, Course, User, Quiz, Questions, Answers
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse, Http404

from quizzes.repositories import QuizRepository, CourseRepository, QuestionRepository, AnswerRepository
from django.core import serializers
from django.template.loader import render_to_string

from django.db import connection
from django.contrib import messages
from django import forms

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


@method_decorator([login_required], name='dispatch')
class CourseListView(ListView,):
	model = Course
	ordering = ('name', )
	context_object_name = 'courses'
	template_name = 'lists/course_list.html'

	def get_queryset(self):
		course = CourseRepository(Course)
		return course.get_by_user__cafedra_owner(self.request.user)

@method_decorator([login_required], name='dispatch')
class CourseCreateView(CreateView):
	model = Course
	fields = ('name', 'description', 'course_cafedra', 'points', 'is_active')
	template_name = 'add/course_add.html'

	def form_valid(self, form):
		course = form.save(commit=False)
		course.owner = self.request.user
		course.save()
		messages.success(self.request, 'The course was created with success! Go ahead and add some quizzes now.')
		return redirect('/teachers/')

#@method_decorator([login_required], name='dispatch')
@login_required
def view_course_quizzes(request, pk):
	quiz = QuizRepository(Quiz)
	quizzes = quiz.get_by_user_course(request.user, pk)
	courses = CourseRepository(Course)
	q_course = Course.objects.get(id = pk)
	owner_id = courses.get_owner_id(pk)
	if(request.user.id == owner_id):
		return render(request, 'lists/quiz_list.html', {'quizzes': quizzes, 'course': q_course})
	raise Http404

class CourseDelete(DeleteView):
	def  get(self, request):
		courseR = CourseRepository(Course)
		cou_id = request.GET.get('id', None)
		owner_id = courseR.get_owner_id(cou_id)
		if request.user.id == owner_id:
			courseR.course_delete(cou_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)

def update_course(request, pk, template_name='update/update_course.html'):
	course= get_object_or_404(Course, pk=pk)
	courses = CourseRepository(Course)
	owner_id = courses.get_owner_id(pk)
	if request.user.id == owner_id:
		form = CourseForm(request.POST or None, instance=course)
		if form.is_valid():
			points = form.cleaned_data["points"]
			quiz = QuizRepository(Quiz)
			all_quiz_points = quiz.get_all_quiz_points(pk)
			if(all_quiz_points <= points):
				form.save()
				messages.success(request, 'Course is updated')
			else:
				messages.error(request, 'Course is not updated. Quizzes in the course have more points than new course points', extra_tags='alert')

			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404

@method_decorator([login_required], name='dispatch')
class QuizListView(ListView,):
	model = Course
	ordering = ('name', )
	context_object_name = 'quizzes'
	template_name = 'lists/quiz_list.html'

	def get_queryset(self):
		return get_by_user_course__course(self, self.request.user, self.request.GET.get('course_id'))

#@method_decorator([login_required], name='dispatch')
@login_required
def quiz_add(request, pk):
	course = get_object_or_404(Course, pk=pk, owner_id=request.user)
	courses = CourseRepository(Course)
	c_points = courses.get_points(pk)
	quizzes = QuizRepository(Quiz)
	all_q_points = quizzes.get_all_quiz_points(pk)
	free_points = c_points - all_q_points
	if request.method == 'POST':
		form = QuizForm(request.POST)
		if form.is_valid():
			quiz = form.save(commit=False)
			quiz.course = course
			quiz.owner = request.user
			if(form.cleaned_data["max_points"] <= free_points):
				quiz.save()
				messages.success(request, 'You may now add question/options to the quiz.')
				return redirect('/teachers/course/%d/quizzes'%pk)
			else:
				messages.error(request, 'You put more points than you have left. Available points: %d'%free_points, extra_tags='alert')
			
	else:
		form = QuizForm()

	return render(request, 'add/quiz_add.html', {'course': course, 'form': form, 'free_points':free_points })


@login_required
def view_quiz_questions(request, pk):
	questionsR = QuestionRepository(Questions)
	questions = questionsR.get_by_quiz_id(pk)
	quiz = QuizRepository(Quiz)
	quizzes = quiz.get_by_id(pk)
	owner_id = quizzes[0].owner_id
	if request.user.id == owner_id:
		return render(request, 'lists/questions_list.html', {'questions': questions, 'quiz': pk, 'quizzes': quizzes})
	raise Http404

class QuizDelete(DeleteView):
	def  get(self, request):
		quizR = QuizRepository(Quiz)
		quiz_id = request.GET.get('id', None)
		owner_id = quizR.get_owner_id(quiz_id)
		if request.user.id == owner_id:
			quizR.quiz_delete(quiz_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)

def update_quiz(request, pk, template_name='update/update_quiz.html'):
	quiz= get_object_or_404(Quiz, pk=pk)
	quizzes = QuizRepository(Quiz)
	owner_id = quizzes.get_owner_id(pk)

	if request.user.id == owner_id:

		course_id = quizzes.get_course_id(pk)
		all_q_points = quizzes.get_all_quiz_points(course_id)
		cur_quiz_points = quizzes.get_quiz_points(pk)
		c_points = quizzes.get_course_points(pk)
		free_points = c_points - all_q_points + cur_quiz_points
		questions = QuestionRepository(Questions)
		sum_question_points = questions.sum_all_quiz_questions_points(pk)

		form = QuizForm(request.POST or None, instance=quiz)
		if form.is_valid():
			quiz = form.save(commit=False)
			form_points_data = form.cleaned_data["max_points"]
			if form_points_data > free_points:
				quiz.max_points = cur_quiz_points
				messages.error(request, 'Available course points: %d. '%free_points, extra_tags='alert')
			if sum_question_points > form_points_data:
				quiz.max_points = cur_quiz_points
				messages.error(request, 'Question points in this quiz are: %d. '%sum_question_points, extra_tags='alert')
			quiz.save()
			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'free_points': free_points, 'sum_questions_points': sum_question_points})
	raise Http404

@login_required
def question_add(request, pk):
	quiz = QuizRepository(Quiz)
	question = QuestionRepository(Questions)
	quiz_points = quiz.get_quiz_points(pk)
	owner_id = quiz.get_owner_id(pk)

	sum_questions_points = question.sum_all_quiz_questions_points(pk)

	free_points = quiz_points - sum_questions_points
	if request.user.id == owner_id:
		if request.method == 'POST':
			form = QuestionForm(request.POST)
			if form.is_valid():
				question = form.save(commit=False)
				question.quiz_id = pk
				if free_points >= form.cleaned_data["points"]:
					question.save()
					messages.success(request, 'You may now add answers/options to the question.')
					return redirect('/teachers/course/quiz/%d/questions/'%pk)
				else:
					messages.error(request, 'You put more points than you have left. Available points: %d'%free_points, extra_tags='alert')
		else:
			form = QuestionForm()

		return render(request, 'add/question_add.html', {'form': form, 'free_points': free_points})
	raise Http404


def update_question(request, pk, template_name='update/update_question.html'):
	question= get_object_or_404(Questions, pk=pk)
	questions = QuestionRepository(Questions)
	owner_id = questions.get_owner_id(pk)

	if request.user.id == owner_id:

		answers = AnswerRepository(Answers)
		sum_answers_points = answers.sum_all_question_answers_points(pk)
		quiz_id = questions.get_quiz_id(pk)
		sum_quiz_questions = questions.sum_all_quiz_questions_points(quiz_id)
		quiz_points = questions.get_quiz_points(pk)
		cur_question_points = questions.get_question_points(pk)
		aval_points = quiz_points - sum_quiz_questions + cur_question_points

		form = QuestionForm(request.POST or None, instance=question)
		if form.is_valid():
			question = form.save(commit=False)
			form_points_data = form.cleaned_data["points"]
			if (form_points_data > aval_points):
				question.points = cur_question_points
				messages.error(request, 'Available course points: %d. '%aval_points)
			if (form_points_data < sum_answers_points):
				question.points = cur_question_points
				messages.error(request, 'Answer points in this question are: %d. '%sum_answers_points)
			question.save()
			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'aval_points': aval_points, 'sum_answers': sum_answers_points})
	raise Http404


class QuestionDelete(DeleteView):
	def  get(self, request):
		questionR = QuestionRepository(Questions)
		que_id = request.GET.get('id', None)
		owner_id = questionR.get_owner_id(que_id)
		if request.user.id == owner_id:
			questionR.question_delete(que_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)


def AnswersView(request, qpk):
	form = AnswerForm()
	answersR = AnswerRepository(Answers)
	answers = answersR.get_by_id_ordered(qpk)
	questions = QuestionRepository(Questions)
	question = questions.get_by_id(qpk)
	owner_id = questions.get_owner_id(qpk)
	qtype = question[0].qtype
	if request.user.id == owner_id and qtype != 'open':
		return render(request, "lists/answers_list.html", {"form": form, "answers": answers, "question_id": qpk, "question": question})
	raise Http404


def add_answer(request, qpk):
	# request should be ajax and method should be POST.
	if request.is_ajax and request.method == "POST":
		# get the form data
		form = AnswerForm(request.POST)
		# save the data and after fetch the object in instance
		if form.is_valid():
			instance = form.save(commit=False)
			answers = AnswerRepository(Answers)
			sum_answers_points = answers.sum_all_question_answers_points(qpk)
			questions = QuestionRepository(Questions)
			question_points = questions.get_question_points(qpk)
			form_points_data = form.cleaned_data["points"]
			free_points = question_points - sum_answers_points

			instance.question_id = qpk
			if form_points_data <= free_points:
				instance.save()
				messages.success(request, 'Success!')
			else:
				instance.points = 0
				instance.save()
				messages.error(request, 'You put more points than you have left. Available points: %d'%free_points)
			# serialize in new friend object in json
			ser_instance = serializers.serialize('json', [ instance, ])
			# send to client side.
			return JsonResponse({"instance": ser_instance}, status=200)
		else:
			# some form errors occured.
			return JsonResponse({"error": form.errors}, status=400)

	# some error occured
	return JsonResponse({"error": ""}, status=400)


class DeleteAnswer(DeleteView):
	def  get(self, request):
		answersR = AnswerRepository(Answers)
		ans_id = request.GET.get('id', None)
		quiz_id = answersR.get_quiz_id(ans_id)
		quiz = QuizRepository(Quiz)
		owner_id = quiz.get_owner_id(quiz_id)

		if request.user.id == owner_id:
			answersR.answer_delete(ans_id)
			data = {
				'deleted': True
			}
			return JsonResponse(data)


def update_answer(request, pk, template_name='update/item_edit_form.html'):
	answer= get_object_or_404(Answers, pk=pk)
	answersR = AnswerRepository(Answers)
	quiz_id = answersR.get_quiz_id(pk)
	quiz = QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(quiz_id)

	if request.user.id == owner_id:
		form = AnswerForm(request.POST or None, instance=answer)

		question_id = answersR.get_question_id(pk)
		sum_answers_points = answersR.sum_all_question_answers_points(question_id)
		question_points = answersR.get_question_points(question_id)
		answer_points = answersR.get_answer_points(pk)
		free_points = question_points - sum_answers_points + answer_points
		if form.is_valid():
			instance = form.save(commit=False)
			form_points_data = form.cleaned_data["points"]
			
			if form_points_data <= free_points:
				messages.success(request, 'Success!')
			else:
				
				instance.points = answer_points
				messages.error(request, 'You put more points than you have left. Available points: %d'%free_points)
			instance.save()
			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'free_points': free_points, 'question_points': question_points})
	raise Http404