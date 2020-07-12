from django.contrib import admin
from quizzes.models import Cafedra, Course, User

# Register your models here.
admin.site.register(Cafedra)
admin.site.register(User)
admin.site.register(Course)
