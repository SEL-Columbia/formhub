from reportlab.pdfgen import canvas
import tempfile
import json
 
def generate_pdf(id_string, user):
    from odk_viewer.models import ParsedInstance  #, DataDictionary
    # dd = DataDictionary.objects.get(id_string=id_string, user=user)
    pis = ParsedInstance.objects.filter(instance__user=user,
                                        instance__xform__id_string=id_string,)
                                        #lat__isnull=False, lng__isnull=False)
    data_for_template = [ 
        {
          'permit_num': pi.to_dict()['obs_nm'],
          'lat': pi.lat,
          'lng': pi.lng
        }
       for pi in pis
    ]

    fname = tempfile.NamedTemporaryFile().name
    can = canvas.Canvas(fname)
    can.drawString(100,750, json.dumps(data_for_template, indent=2))
    can.save()

    result = None
    with file(fname, "rb") as pdf_file:
        result = pdf_file.read()

    return result

    # for pi in pis:
    #     # read the survey instances
    #     data_for_display = pi.to_dict()
    #     xpaths = data_for_display.keys()
    #     xpaths.sort(cmp=pi.data_dictionary.get_xpath_cmp())
    #     label_value_pairs = [
    #         (cached_get_labels(xpath),
    #          data_for_display[xpath]) for xpath in xpaths
    #         if not xpath.startswith(u"_")]
    #     table_rows = []
    #     for key, value in label_value_pairs:
    #         table_rows.append('<tr><td>%s</td><td>%s</td></tr>' % (key, value))
    #     img_urls = []
    #     img_url = ""
    #     data_for_template.append({
    #         'name': id_string,
    #         'id': pi.id,
    #         'lat': pi.lat,
    #         'lng': pi.lng,
    #         'image_urls': img_urls,
    #         'table': '<table border="1"><a href="#"><img width="210" '
    #                  'class="thumbnail" src="%s" alt=""></a>%s'
    #                  '</table>' % (img_url, ''.join(table_rows))})
