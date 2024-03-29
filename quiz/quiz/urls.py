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
from quizzes.teachers import *
from quizzes.students import *
from quizzes.adminView import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('quiz/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('quiz/signup', TemplateView.as_view(template_name='registration/signup.html'), name='signup'),
    path('accounts/signup/teacher/', TeacherSignUpView.as_view(), name='teacher_signup'),
    path('accounts/signup/students/', StudentSignUpView.as_view(), name='student_signup'),

    path('teachers/', include(([
       path('', CourseListView.as_view(template_name='teachers/lists/course_list.html'), name='course_list'),
       path('course/', CourseCreateView.as_view(template_name='teachers/add/course_add.html'), name='course_add'),
       path('course/delete/', CourseDelete.as_view(), name='course_delete'),
       path('course/<int:pk>/edit/', update_course, name = "update_course"),
       path('course/<int:pk>/quizzes/', view_course_quizzes, name='quiz_list'),
       path('course/<int:pk>/view/', view_course_info, name = "view_course"),
       path('course/activate/', ActivateDeactivateCourse.as_view(), name='course_activate'),
       path('course/<int:pk>/quiz/add/', quiz_add, name='quiz_add'),
       path('course/quiz/delete/', QuizDelete.as_view(), name='quiz_delete'),
       path('course/quiz/deactivate/', DeactivateQuiz.as_view(), name='deactivate_quiz'),
       path('course/quiz/<int:pk>/edit/', update_quiz, name = "update_quiz"),
       path('course/quiz/<int:pk>/activate/', activate_quiz, name = "activate_quiz"),
       path('course/quiz/<int:pk>/questions/', view_quiz_questions, name='questions_list'),
       path('course/quiz/<int:pk>/view/', view_quiz_info, name = "view_quiz"),
       path('course/quiz/<int:pk>/question/add/', question_add, name='question_add'),
       path('course/quiz/question/delete',  QuestionDelete.as_view(), name='delete_question'),
       path('course/quiz/question/<int:pk>/edit/', update_question, name = "update_question"),
       path('course/quiz/question/<int:pk>/view/', view_question_info, name = "view_question"),
       path('course/quiz/question/<int:qpk>/answers/add/', AnswersView, name='answers_lists_add'),
       path('course/quiz/question/<int:qpk>/answers/add/success', add_answer, name = "add_answer"),
       path('course/quiz/question/answers/delete',  DeleteAnswer.as_view(), name='delete_answer'),
       path('course/quiz/question/answers/<int:pk>/edit/', update_answer, name = "item_edit"),

       path('course/quiz/<int:pk>/incode/update', quiz_update_in_code, name = "quiz_update_in_code"),
       path('course/<int:pk>/incode/update', course_update_in_code, name = "course_update_in_code"),

       path('course/quiz/<int:pk>/answers/check/', view_quiz_for_check, name = "view_quiz_for_check"), 
       path('course/quiz/<int:pk>/answers/check/student/<int:spk>/', get_answers_for_check, name = "get_answers_for_check"),
       path('course/quiz/<int:pk>/answers/check/student/<int:spk>/finish/', save_checked_answers, name = "save_checked_answers"),
       path('course/quiz/<int:pk>/grades/', view_students_quiz_grades, name = "view_students_quiz_grades"),
       path('course/quiz/<int:pk>/preview/', quiz_preview, name = "quiz_preview"),
       path('course/quiz/<int:pk>/student/<int:spk>/view/', student_quiz_view, name = "student_quiz_view"),
       path('course/<int:pk>/participants/list/', course_participants_list, name = "course_participants_list"),

       path('grammar/', grammar_checker, name = "grammar_checker"),
       path('course/quiz/question/<int:qpk>/answers/add/test_grammar', test_grammar, name = "test_grammar"),
    ], 'quizzes'), namespace='teachers')),

    path('students/', include(([
       path('', view_all_not_joined_couses, name='course_list_student'),
       path('course/<int:pk>/join/', join_course, name = "join_course"),
       path('course/quiz/<int:pk>/join/', join_quiz, name = "join_quiz"),
       path('course/joined/', view_all_joined_couses, name = "course_joined_courses"),
       path('course/quiz/<int:pk>/confirm_take/', take_quiz_confirm, name = "take_quiz_confirm"),
       path('course/quiz/<int:pk>/take/', take_quiz, name = "take_quiz"),
       path('course/<int:pk>/quizzes/', view_course_active_quizzes, name = "view_course_active_quizzes"),
       path('course/quiz/<int:pk>/finish/', finish_test, name = "finish_test"),
       path('course/quiz/<int:pk>/view/', student_view_quiz_info, name = "student_view_quiz_info"),
       path('course/quiz/<int:pk>/graded/view/', graded_quiz_view, name = "graded_quiz_view"),
       
    ], 'quizzes'), namespace='students')),

    path('train/', include(([
       path('', train_page, name = "train_page"),
       path('tags/', train, name = "train"),
       path('progress/', get_progress, name = "get_progress"),
    ], 'quizzes'), namespace='train')),

    path('test/', include(([
       path('', test_page, name = "test_page"),
       path('lang/', test, name = "test"),
    ], 'quizzes'), namespace='test')),
]

