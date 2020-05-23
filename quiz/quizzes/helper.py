import random
import string

def generate_code(lettersCount = 4, digitsCount = 2):
    sampleStr = ''.join((random.choice(string.ascii_letters) for i in range(lettersCount)))
    sampleStr += ''.join((random.choice(string.digits) for i in range(digitsCount)))
    
    # Convert string to list and shuffle it to mix letters and digits
    sampleList = list(sampleStr)
    random.shuffle(sampleList)
    finalString = ''.join(sampleList)
    return finalString

def check_grades(exelent, verygood, good, bad):
	if exelent > verygood and verygood > good and good > bad:
		return True
	else:
		return False
