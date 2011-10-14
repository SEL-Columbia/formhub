from odk_viewer.models import ParsedInstance
from odk_logger.models import Instance
from utils.reinhardt import json_response
from django.shortcuts import render_to_response


def survey_responses(request, pk):
    # todo: do a good job of displaying hierarchical data
    pi = ParsedInstance.objects.get(instance=pk)
    data = pi.to_dict()

    # get rid of keys with leading underscores
    data_for_display = {}
    for k, v in data.items():
        if not k.startswith(u"_"):
            data_for_display[k] = v

    xpaths = data_for_display.keys()
    xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
    label_value_pairs = [
        (pi.data_dictionary.get_label(xpath),
         data_for_display[xpath]) for xpath in xpaths]

    return render_to_response('survey.html', {
            'label_value_pairs': label_value_pairs,
            'image_urls': image_urls(pi.instance),
            })


def image_urls(instance):
    return [a.media_file.url for a in instance.attachments.all()]
