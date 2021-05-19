from rest_framework import serializers

class LanguagesSerializer(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	name = serializers.CharField(max_length=15, required=True, allow_blank=False)
	abr = serializers.CharField(max_length=6, required=True, allow_blank=False)


class LearnSetsSerializer(serializers.Serializer):
	id = serializers.IntegerField(read_only=True)
	set_name = serializers.CharField()
	lang_id = serializers.HyperlinkedRelatedField(view_name='api:languages-detail', source = 'languages', read_only=True)
	add_date = serializers.DateTimeField()

class AnswersSerializer(serializers.Serializer):
	name = serializers.CharField()
	question = serializers.HyperlinkedRelatedField(view_name='api:question_id', source = 'questions', read_only=True)
	points = serializers.FloatField(default=0)
	correct = serializers.BooleanField(default=True)