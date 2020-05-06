"""quiz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from quizzes.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('quiz/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('quiz/signup', TemplateView.as_view(template_name='registration/signup.html'), name='signup'),
    path('accounts/signup/teacher/', TeacherSignUpView.as_view(), name='teacher_signup'),

    path('teachers/', include(([
       path('', CourseListView.as_view(template_name='lists/course_list.html'), name='course_list'),
       path('course/', CourseCreateView.as_view(template_name='add/course_add.html'), name='course_add'),
       path('course/<int:pk>/quizzes/', view_course_quizzes, name='quiz_list'),
       path('course/<int:pk>/quiz/add/', quiz_add, name='quiz_add'),
       path('course/delete/<int:pk>/', CourseDeleteView.as_view(template_name='delete/course_delete_confirm.html'), name='course_delete'),
       path('course/quiz/questions/<int:pk>/', view_quiz_questions, name='questions_list'),
       path('course/quiz/<int:pk>/question/add/', question_add, name='question_add'),
       path('course/quiz/question/<int:qpk>/answers/add/', AnswersView, name='answers_lists_add'),
       path('course/quiz/question/<int:qpk>/answers/add/success', add_answer, name = "add_answer"),
       path('course/quiz/question/answers/delete',  DeleteAnswer.as_view(), name='delete_answer'),
       path('course/quiz/question/answers/<int:pk>/edit/', update_answer, name = "item_edit"),

       path('course/quiz/question/<int:pk>/edit/', update_question, name = "update_question"),



    ], 'quizzes'), namespace='teachers')),
]

