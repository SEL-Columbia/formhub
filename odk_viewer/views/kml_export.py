from django.shortcuts import render_to_response
from django.template import RequestContext
from odk_viewer.models import ParsedInstance



def kml_export(request, id_string):
    # read the locations from the database
    context = RequestContext(request)
    context.message="HELLO!!"
    #locations = ParsedInstance.objects.values('lat', 'lng', 'instance').filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False)
    #pk = ParsedInstance.objects.values('instance').filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False) 
    pis = ParsedInstance.objects.filter(instance__user=request.user, instance__xform__id_string=id_string, lat__isnull=False, lng__isnull=False) 
    #locations = Location.objects.all()
    #print (ParsedInstance.objects.values)
    #context.locations = locations
    #print context.locations
    
    data_for_template = []
    for pi in pis:
        # read the survey instances
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
        table_rows = []
        for key, value in label_value_pairs:
            table_rows.append('<tr><td>%s</td><td>%s</td></tr>' % (key, value))
        print '<table>%s</table>' % (''.join(table_rows))
        data_for_template.append({"lat": pi.lat, "lng": pi.lng, "table": '<table>%s</table>' % (''.join(table_rows))})
        
    context.data = data_for_template
    #import pdb; pdb.set_trace()
    response = render_to_response("facilities_template.kml",
    context_instance=context,
    mimetype="application/vnd.google-earth.kml+xml")
    response['Content-Disposition'] = 'attachment; filename=facilities.kml'
    return response


    

