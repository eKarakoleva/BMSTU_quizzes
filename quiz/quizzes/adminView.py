import quizzes.repositories as repo
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .grammar.Trainer import train_packet
from .grammar.lang_abr import languages
import quizzes.adminViewOperations as avo
from quizzes.models import Languages, Tagset
from django.http import JsonResponse
from quizzes.grammar.TestMethod import TestMethod

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

@login_required
def test_page(request):
	return render(request, 'grammar/test_page.html', {'langs': languages})

@login_required
def test(request):
	lang = request.GET.get('lang', None)
	tm = TestMethod(lang)
	tm.read_ethalon_sents_from_file()
	#tm.test_results('spelling')
	#tm.test_results('order')
	#tm.test_results('translate')
	#tm.test_results('not_ethalon')
	#tm.test_results('form')
	#tm.test_results('spelling')
	tm.test_results('combine')
	data = {
		'activated': True
	}
	return JsonResponse(data)