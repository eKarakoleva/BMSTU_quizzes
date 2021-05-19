import quizzes.repositories as repo
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages 
from django.contrib.auth.decorators import login_required

from .grammar.Trainer import Trainer, train_packet
from .grammar.lang_abr import languages, abr_lang 
import quizzes.adminViewOperations as avo
from quizzes.models import Languages, Tagset, BiGramms, TriGramms, LearnSets
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect

@login_required
def train_page(request):
	avo.fill_languages()
	avo.fill_LearnSets()
	return render(request, 'grammar/train_page.html', {'langs': languages, 'packs': train_packet})

@login_required
def train(request):
	lang = request.GET.get('lang', None)
	packet = request.GET.get('packet', None)
	langRepo = repo.LanguagesRepository(Languages)
	lang_id = langRepo.get_id_by_abr(lang)
	
	
	tagsetRepo = repo.TagsetRepository(Tagset)
	tags_empty = tagsetRepo.is_empty(lang_id)
	ret_status = avo.train_tags_model(lang, packet, request.user.id)
	print("RET_STATUS: ", ret_status)
	key = 'id_' + str(request.user.id)
	session_exist = request.session.get(key)

	if session_exist:
		print("\n\nSESSSION CORPUS: ", session_exist['corpus'])
		if not ret_status and session_exist['corpus'] != '':
			print("SESSION_AFTER: ", session_exist)
			if session_exist:
				del request.session[key]

	data = {
		'activated': True
	}
	return JsonResponse(data)


@login_required
def get_progress(request):
	process, corpus = avo.get_progress(request.user.id)		
	data = {
		'status': process,
		'corpus': corpus
	}
	return JsonResponse(data)