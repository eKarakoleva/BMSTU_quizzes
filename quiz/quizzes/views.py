from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)
from quizzes.forms import TeacherSignUpForm, QuizForm, QuestionForm, AnswerForm
from quizzes.models import Cafedra, Course, User, Quiz, Questions, Answers
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from quizzes.repositories import QuizRepository, CourseRepository, QuestionRepository, AnswerRepository


from django.http import JsonResponse
from django.core import serializers
from django.template.loader import render_to_string
from django.http import Http404


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
	fields = ('name', 'description', 'course_cafedra')
	template_name = 'add/course_add.html'

	def form_valid(self, form):
		course = form.save(commit=False)
		course.owner = self.request.user
		course.save()
		messages.success(self.request, 'The course was created with success! Go ahead and add some quizzes now.')
		return redirect('/teachers/')

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
	if request.method == 'POST':
		form = QuizForm(request.POST)
		if form.is_valid():
			quiz = form.save(commit=False)
			quiz.course = course
			quiz.owner = request.user
			quiz.save()
			messages.success(request, 'You may now add question/options to the quiz.')
			return redirect('/teachers/course/%d/quizzes'%pk)
	else:
		form = QuizForm()

	return render(request, 'add/quiz_add.html', {'course': course, 'form': form})

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

class CourseDeleteView(DeleteView):
	model = Course
	template_name = 'delete/course_delete_confirm.html'

	def delete(self, request, *args, **kwargs):
		courses = CourseRepository(Course)
		owner_id = courses.get_owner_id(self.kwargs['pk'])
		if(request.user == owner_id):
			course = self.get_object()
			messages.success(request, 'The course %s was deleted with success!' % course.name)
			return super().delete(request, *args, **kwargs)
		raise Http404

	def get_success_url(self):
		return reverse('teachers:course_list')


@login_required
def view_quiz_questions(request, pk):
	questionsR = QuestionRepository(Questions)
	questions = questionsR.get_by_quiz_id(pk)
	quiz = QuizRepository(Quiz)
	quizzes = quiz.get_by_id(pk)
	owner_id = quiz.get_owner_id(pk)
	if request.user.id == owner_id:
		return render(request, 'lists/questions_list.html', {'questions': questions, 'quiz': pk, 'quizzes': quizzes})
	raise Http404


@login_required
def question_add(request, pk):
	quiz = QuizRepository(Quiz)
	owner_id = quiz.get_owner_id(pk)
	if request.user.id == owner_id:
		if request.method == 'POST':
			form = QuestionForm(request.POST)
			if form.is_valid():
				question = form.save(commit=False)
				question.quiz_id = pk
				question.save()
				messages.success(request, 'You may now add answers/options to the question.')
				return redirect('/teachers/course/quiz/%d/questions/'%pk)
		else:
			form = QuestionForm()

		return render(request, 'add/question_add.html', {'form': form})
	raise Http404


def AnswersView(request, qpk):
	form = AnswerForm()
	answersR = AnswerRepository(Answers)
	answers = answersR.get_by_id_ordered(qpk)
	questions = QuestionRepository(Questions)
	question = questions.get_by_id(qpk)
	owner_id = questions.get_owner_id(qpk)
	if request.user.id == owner_id:
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
			instance.question_id = qpk
			instance.save()
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
		id1 = request.GET.get('id', None)
		answersR = AnswerRepository(Answers)
		answersR.answer_delete(id1)
		data = {
			'deleted': True
		}
		return JsonResponse(data)


def update_answer(request, pk, template_name='update/item_edit_form.html'):
	answer= get_object_or_404(Answers, pk=pk)
	answersR = AnswerRepository(Answers)
	owner_id = answersR.get_owner_id(pk)
	if request.user.id == owner_id:
		form = AnswerForm(request.POST or None, instance=answer)
		if form.is_valid():
			form.save()
			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk, 'owner_id': owner_id})
	raise Http404


def update_question(request, pk, template_name='update/update_question.html'):
	question= get_object_or_404(Questions, pk=pk)
	questions = QuestionRepository(Questions)
	owner_id = questions.get_owner_id(pk)
	if request.user.id == owner_id:
		form = QuestionForm(request.POST or None, instance=question)
		#raise Exception({owner_id})
		if form.is_valid():
			form.save()
			return HttpResponse(render_to_string('update/item_edit_form_success.html'))
		return render(request, template_name, {'form':form, 'id': pk})
	raise Http404


