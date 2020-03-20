from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)
from quizzes.forms import TeacherSignUpForm, QuizForm
from quizzes.models import Cafedra, Course, User, Quiz
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

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
        queryset = Course.objects.filter(owner_id = self.request.user).select_related('course_cafedra').select_related('owner')
        return queryset

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
        queryset = Quiz.objects.filter(owner_id = self.request.user, course_id = self.request.GET.get('course_id')).select_related('course')
        return queryset

@method_decorator([login_required], name='dispatch')
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
            return redirect('/teachers/course/%d/'%pk)
    else:
        form = QuizForm()

    return render(request, 'add/quiz_add.html', {'course': course, 'form': form})

@method_decorator([login_required], name='dispatch')
def view_course_quizzes(request, pk):
	quizzes = Quiz.objects.filter(owner_id=request.user, course_id = pk)
	q_course = Course.objects.get(id = pk)
	return render(request, 'lists/quiz_list.html', {'quizzes': quizzes, 'course': q_course})

class CourseDeleteView(DeleteView):
    model = Course
    template_name = 'delete/course_delete_confirm.html'

    def delete(self, request, *args, **kwargs):
        course = self.get_object()
        messages.success(request, 'The course %s was deleted with success!' % course.name)
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('teachers:course_list')