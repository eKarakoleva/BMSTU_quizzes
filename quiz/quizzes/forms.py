from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from quizzes.models import (User, Cafedra, Course, Quiz, Questions, QuestionType, Answers)

class TeacherSignUpForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'cafedra')
		

	def save(self, commit=True):
		user = super().save(commit=False)
		user.is_teacher = True
		if commit:
			user.save()
		return user

class CourseForm(forms.ModelForm):
	class Meta:
		model = Course
		fields = ('name', 'description', 'course_cafedra', 'points', 'is_active')

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
		fields = ('name', 'description', 'max_points', 'min_points', 'is_active')

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
		self.fields['points'].queryset = Answers.objects.filter(id=76)
