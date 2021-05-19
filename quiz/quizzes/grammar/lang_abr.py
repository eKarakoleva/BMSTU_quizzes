abr_lang = {
    'en': "english",
    'ru': "russian",
    'bg': "bulgarian"

}

lang_abr = {
    'english': 'en',
    'russian': 'ru',
    'bulgarian': 'bg'
}

languages = ['en', 'ru']

def lang_to_abr(lang):
    if lang not in lang_abr:
        return lang
    else:
        return lang_abr[lang]

def abr_to_lang(abr):
    if abr not in abr_lang:
        return abr
    else:
        return abr_lang[abr]