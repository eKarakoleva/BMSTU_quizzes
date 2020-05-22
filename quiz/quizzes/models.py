from django.db import models
from django.contrib.auth.models import AbstractUser

class Cafedra(models.Model):
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name

class User(AbstractUser):
	is_student = models.BooleanField(default=False)
	is_teacher = models.BooleanField(default=False)
	cafedra = models.OneToOneField(Cafedra, on_delete=models.PROTECT, related_name='user_cafedra')


class Course(models.Model):
	name = models.TextField()
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_owner', unique=False)
	description = models.CharField(max_length=200)
	course_cafedra = models.ForeignKey(Cafedra, on_delete=models.CASCADE)
	is_active = models.BooleanField(default=False)
	points = models.IntegerField(default=200)


	def __str__(self):
		return self.name


class Quiz(models.Model):
	name = models.TextField()
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_owner', unique=False)
	description = models.TextField(blank=True)
	course = models.ForeignKey(Course, on_delete=models.CASCADE,  related_name='quiz_course', unique=False)
	max_points = models.IntegerField(default=100)
	min_points = models.IntegerField(default=50)
	done = models.BooleanField(default=False)
	is_active = models.BooleanField(default=False)

	def __str__(self):
		return self.name

class QuestionType(models.Model):
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name

class Questions(models.Model):
	name = models.TextField()
	quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='quiz_id', unique=False)
	description = models.TextField(blank=True)
	points = models.IntegerField(default=0)
	QUESTION_TYPES = [
		('multiple', 'multiple'),
		('single', 'single'),
		('compare', 'compare'),
		('open', 'open'),
	]

	qtype = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single',)
	done = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class Answers(models.Model):
	name = models.TextField()
	question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='question_id', unique=False)
	points = models.IntegerField(default=0)
	correct = models.BooleanField(default=True)

	def __str__(self):
		return self.name