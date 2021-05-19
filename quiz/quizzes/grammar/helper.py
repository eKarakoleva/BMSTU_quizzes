import re

def process_sent(sent, tag_types, posTagger, make_all_lower = True):
    sent = re.sub(r"\([^()]*\)", "", sent)
    if make_all_lower:
        sent = sent.lower()
    tags = posTagger.tag(sent)
    temp = []
    for all_info in tags:
        a = all_info.split(" ")
        tag = a[0].split()[1]
        if tag != "," and tag != 'SENT':
            if tag not in tag_types:
                tag_types.append(tag)
            temp.append(tag)
    return tag_types, temp
