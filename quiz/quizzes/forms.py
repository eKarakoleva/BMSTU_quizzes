from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from quizzes.models import (User, Cafedra, Course, Quiz, Questions, QuestionType, Answers, StudentAnswers)
from quizzes.repositories import AnswerRepository

class TeacherSignUpForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email', 'first_name', 'surname', 'last_name', 'cafedra')

	def __init__(self, *args, **kwargs):
		super(TeacherSignUpForm, self).__init__(*args, **kwargs)

		for key in self.fields:
			self.fields[key].required = True 

	def save(self, commit=True):
		user = super().save(commit=False)
		user.is_teacher = True
		if commit:
			user.save()
		return user

class StudentSignUpForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email', 'first_name', 'surname', 'last_name', 'cafedra')

	def __init__(self, *args, **kwargs):
		super(StudentSignUpForm, self).__init__(*args, **kwargs)

		for key in self.fields:
			self.fields[key].required = True 
			
	def save(self, commit=True):
		user = super().save(commit=False)
		user.is_student = True
		if commit:
			user.save()
		return user

class CourseForm(forms.ModelForm):
	class Meta:
		model = Course
		fields = ('name', 'description', 'course_cafedra', 'points')

		widgets = {
			'description': forms.Textarea(attrs={'rows':4, 'cols':15}),
			'name': forms.Textarea(attrs={'rows':4, 'cols':15}),
		}
	def __init__(self, *args, **kwargs):
		super(CourseForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

class QuizForm(forms.ModelForm):
	class Meta:
		model = Quiz
		fields = ('name', 'description', 'max_points')

		widgets = {
			'description': forms.Textarea(attrs={'rows':4, 'cols':15}),
			'name': forms.Textarea(attrs={'rows':4, 'cols':15}),
		}

	def __init__(self, *args, **kwargs):
		super(QuizForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

class QuizInCodeForm(forms.ModelForm):
	class Meta:
		model = Quiz
		fields = ('in_code', )

	def __init__(self, *args, **kwargs):
		super(QuizInCodeForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

		self.fields['in_code'].widget.attrs['readonly'] = True

class QuizActivateForm(forms.ModelForm):
	class Meta:
		model = Quiz
		fields = ('max_points', 'good_points', 'min_points', 'timer_minutes')

	def __init__(self, *args, **kwargs):
		super(QuizActivateForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

class QuestionForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(QuestionForm, self).__init__(*args, **kwargs)
		
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})
	class Meta:
		model = Questions
		fields = ('name', 'qtype','description', 'points')

		widgets = {
			'description': forms.Textarea(attrs={'rows':4, 'cols':15}),
			'name': forms.Textarea(attrs={'rows':4, 'cols':15}),
		}

class AnswerForm(forms.ModelForm):
	class Meta:
		model = Answers
		fields = ('name', 'points', 'correct')

		widgets = {
			'name': forms.Textarea(attrs={'rows':4, 'cols':15}),
		}

	def __init__(self, *args, **kwargs):
		super(AnswerForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

#STUDENTS

class ActivationCodeForm(forms.ModelForm):
	class Meta:
		model = Answers
		fields = ('name', 'points', 'correct')

		widgets = {
			'name': forms.Textarea(attrs={'rows':4, 'cols':15}),
		}

	def __init__(self, *args, **kwargs):
		super(AnswerForm, self).__init__(*args, **kwargs)

		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

class TakeQuizForm(forms.ModelForm):

	class Meta:
		model = StudentAnswers
		fields = ('question','answer')

	def __init__(self, *args, **kwargs):
		super(TakeQuizForm, self).__init__(*args, **kwargs)