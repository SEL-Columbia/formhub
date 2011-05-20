from parsed_xforms.models import ParsedInstance, DataDictionary
from xform_manager.models import Instance
from django.http import HttpResponse
from utils import json_response
from deny_if_unauthorized import deny_if_unauthorized

@deny_if_unauthorized()
def survey_responses(request, pk):
    instance = Instance.objects.get(pk=pk)
    parsed_instance = instance.parsed_instance
    data = parsed_instance.to_dict()

    # get rid of keys with leading underscores
    data_for_display = {}
    for k, v in data.items():
        if not k.startswith(u"_"):
            data_for_display[k] = v

    try:
        xform = parsed_instance.instance.xform
        data_dictionary = DataDictionary.objects.get(xform=xform)
    except DataDictionary.DoesNotExist:
        data_dictionary = None
    if data_dictionary:
        xpaths = data_for_display.keys()
        xpaths.sort(cmp=data_dictionary.get_xpath_cmp())
        label_value_pairs = []
        for xpath in xpaths:
            label = data_dictionary.get_label(xpath)
            if label==u"{}": label = xpath
            value = data_for_display[xpath]
            if type(value)==unicode:
                pretty_value = data_dictionary.get_label(xpath + u"/" + value)
                if pretty_value: value = pretty_value
            if value:
                label_value_pairs.append((label, value))
    else:
        label_value_pairs = data_for_display.items()

    return json_response(label_value_pairs)

@deny_if_unauthorized()
def survey_media_files(request, pk):
    instance = Instance.objects.get(pk=pk)
    parsed_instance = instance.parsed_instance
    attachments = parsed_instance.instance.attachments
    urls = [a.media_file.url for a in attachments.all()]
    return json_response(urls)
