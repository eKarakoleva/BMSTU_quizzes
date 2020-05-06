# Generated by Django 3.1.dev20200220140547 on 2020-05-03 12:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_auto_20200320_1250'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AlterField(
            model_name='quiz',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_course', to='quizzes.Course'),
        ),
        migrations.CreateModel(
            name='Questions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=200)),
                ('points', models.IntegerField(default=100)),
                ('qtype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizzes.QuestionType')),
                ('quiz', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_id', to='quizzes.Quiz')),
            ],
        ),
    ]
