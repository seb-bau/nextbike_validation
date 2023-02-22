import random
import re
import string


def email_is_valid(p_email):
    email_validation_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(email_validation_regex, p_email):
        return True
    else:
        return False


def random_string(number_of_characters=6, without_punctuation=True):
    if without_punctuation:
        characters = string.ascii_letters + string.digits
    else:
        characters = string.ascii_letters + string.digits + string.punctuation
    t_random_string = ''.join(random.choice(characters) for _ in range(number_of_characters))
    return t_random_string
