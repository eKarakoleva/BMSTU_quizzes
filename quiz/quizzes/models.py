from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Cafedra(models.Model):
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name

class User(AbstractUser):
	alphanumeric = RegexValidator(r'^[A-Za-z\-]*$', 'Only alphanumeric characters and dashes are allowed.')

	surname = models.CharField(max_length=100, validators=[alphanumeric])
	first_name = models.CharField(max_length=50, validators=[alphanumeric])
	last_name = models.CharField(max_length=100, validators=[alphanumeric])
	
	is_student = models.BooleanField(default=False)
	is_teacher = models.BooleanField(default=False)
	cafedra = models.ForeignKey(Cafedra, on_delete=models.PROTECT, related_name='user_cafedra',blank=True, null=True)

def create_superuser(self, email, password, cafedra_id):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email = email,
            password=password,
            cafedra=3,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Course(models.Model):
	name = models.TextField()
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_owner', unique=False)
	description = models.TextField(blank=True)
	course_cafedra = models.ForeignKey(Cafedra, on_delete=models.CASCADE)
	is_active = models.BooleanField(default=False)
	points = models.FloatField(default=200)
	in_code = models.CharField(max_length=6, blank=True)

	def __str__(self):
		return self.name


class Quiz(models.Model):
	name = models.TextField()
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_owner', unique=False)
	description = models.TextField(blank=True)
	course = models.ForeignKey(Course, on_delete=models.CASCADE,  related_name='quiz_course', unique=False)
	max_points = models.FloatField(default=100)
	good_points = models.FloatField(default=0)
	min_points = models.FloatField(default=0)
	timer_minutes = models.IntegerField(default=0)
	#done = models.BooleanField(default=False)
	is_active = models.BooleanField(default=False)
	in_code = models.CharField(max_length=6, blank=True)


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
	points = models.FloatField(default=0)
	QUESTION_TYPES = [
		('multiple', 'multiple'),
		('single', 'single'),
		('compare', 'compare'),
		('open', 'open'),
		('grammar', 'grammar'),
	]

	qtype = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single',)
	done = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class Answers(models.Model):
	name = models.TextField()
	question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='question_id', unique=False)
	points = models.FloatField(default=0)
	correct = models.BooleanField(default=True)

	def __str__(self):
		return self.name

class CourseParticipants(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_id', unique=False) #student
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_id', unique=False)
	join_date = models.DateTimeField(auto_now=True, unique=False)

	def __str__(self):
		return '{} --- {} '.format(self.user.username, self.course.name)


class QuizSolveRecord(models.Model):
	
	def __str__(self):
		return '{} --- {} '.format(self.student.username, self.quiz.name)

	quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='qsrquiz_id', unique=False)
	student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_id', unique=False)
	time_start = models.DateTimeField(auto_now_add=True)
	#time_end = models.DateTimeField(auto_now=True)
	time_end = models.DateTimeField(auto_now_add=True)
	points = models.FloatField(default=0)
	is_fully_checked = models.BooleanField(null = True)


class StudentAnswers(models.Model):

	solve_info = models.ForeignKey(QuizSolveRecord, on_delete=models.CASCADE, related_name='sasolve_info', unique=False)
	question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='answer_question', unique=False)
	answer = models.ForeignKey(Answers, on_delete=models.CASCADE, related_name='studanswer_id', unique=False)

class StudentOpenAnswers(models.Model):

	solve_info = models.ForeignKey(QuizSolveRecord, on_delete=models.CASCADE, related_name='sosolve_info', unique=False)
	question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='oanswer_question', unique=False)
	answer = models.TextField(blank=True)
	points = models.FloatField(default=0)


class Languages(models.Model):
	name = models.CharField(max_length=15)
	abr = models.CharField(max_length=6)

class LearnSets(models.Model):
	set_name = models.TextField()
	lang = models.ForeignKey(Languages, on_delete=models.CASCADE, related_name='lang_learn_tagset', unique=False)
	add_date = models.DateTimeField(auto_now_add=True)

class Tagset(models.Model):
	tag = models.TextField()
	lang = models.ForeignKey(Languages, on_delete=models.CASCADE, related_name='lang_tagset', unique=False)

class BiGramms(models.Model):
	tag1 = models.ForeignKey(Tagset, on_delete=models.CASCADE, related_name='tag_bi_1', unique=False, null=True)
	tag2 = models.ForeignKey(Tagset, on_delete=models.CASCADE, related_name='tag_bi_2', unique=False, null=True)
	freq = models.CharField(max_length=10)
	lang = models.ForeignKey(Languages, on_delete=models.CASCADE, related_name='lang_bi', unique=False)
	learn_set = models.ForeignKey(LearnSets, on_delete=models.CASCADE, related_name='learn_set_bi', unique=False)

class TriGramms(models.Model):
	tag1 = models.ForeignKey(Tagset, on_delete=models.CASCADE, related_name='tag_tri_1', unique=False, null=True)
	tag2 = models.ForeignKey(Tagset, on_delete=models.CASCADE, related_name='tag_tri_2', unique=False, null=True)
	tag3 = models.ForeignKey(Tagset, on_delete=models.CASCADE, related_name='tag_tri_3', unique=False, null=True)
	freq = models.CharField(max_length=10)
	lang = models.ForeignKey(Languages, on_delete=models.CASCADE, related_name='lang_tri', unique=False)
	learn_set = models.ForeignKey(LearnSets, on_delete=models.CASCADE, related_name='learn_set_tri', unique=False)


class GrammarQuestionSanctions(models.Model):
	question = models.ForeignKey(Questions, on_delete=models.CASCADE, related_name='question_id_grammar', unique=False)
	lang = models.ForeignKey(Languages, on_delete=models.CASCADE, related_name='lang_question', unique=False)
	spelling_points = models.FloatField(default=0)
	grammar_points = models.FloatField(default=0)
	translate_points = models.FloatField(default=0)