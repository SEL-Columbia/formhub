QUESTION_TYPES_TO_EXCLUDE = [
    u'note',
]

def question_types_to_exclude(_type):
    return _type in QUESTION_TYPES_TO_EXCLUDE
