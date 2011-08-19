from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from facility_views.models import FacilityTable, MapLayerDescription
from nga_districts.models import LGA, Zone, State
from django.db.models import Count
import json

@login_required
def dashboard(request, reqpath):
    if request.method == "POST":
        lgaid = request.POST['lga']
        if LGA.objects.filter(unique_slug=lgaid).count() > 0:
            return HttpResponseRedirect("/~%s" % lgaid)
        else:
            return HttpResponseRedirect("/~")
    context = RequestContext(request)
    context.data_loading_count = LGA.objects.filter(data_load_in_progress=True).count()
    context.site_title = "NMIS Nigeria"
    lga = None
    context.active_districts = active_districts()
    context.nav_zones = get_nav_zones(filter_active=True)
    mls = []
    for map_layer in MapLayerDescription.objects.all():
        mls.append(model_to_dict(map_layer))
    context.layer_details = json.dumps(mls)
    if not reqpath == "":
        req_lga_id = reqpath.split("/")[0]
        try:
            lga = LGA.objects.get(unique_slug=req_lga_id)
        except:
            lga = None
        if lga == None:
            return HttpResponseRedirect("/~")
    if lga == None:
        return country_view(context)
    else:
        context.lga = lga
        return lga_view(context)

def test_map(request):
    return render_to_response("test_map.html")

def get_nav_zones(filter_active=False):
    zone_list = Zone.objects.all().values('id', 'name')
    zones = {}
    for zone in zone_list:
        zid = zone.pop('id')
        zone['states'] = []
        zones[zid] = zone

    state_list = State.objects.all().values('id', 'zone_id', 'name')
    if filter_active:
        lga_list = LGA.objects.annotate(facility_count=Count('facilities')). \
                        filter(facility_count__gt=0). \
                        values('unique_slug', 'name', 'state_id')
    else:
        lga_list = LGA.objects.all().values('unique_slug', 'name', 'state_id')
    states = {}
    for state in state_list:
        sid = state.pop('id')
        zid = state.pop('zone_id')
        state['lgas'] = []
        states[sid] = state
        zones[zid]['states'].append(state)
    for lga in lga_list:
        sid = lga.pop('state_id')
        states[sid]['lgas'].append(lga)
    for state in state_list:
        state['lga_count'] = len(state['lgas'])
    return zone_list

def get_nav_zones_inefficient():
    zones = Zone.objects.all()
    nav_list = []
    for zone in zones:
        nav_list.append({
            'name': zone.name,
            'states': state_data(zone)
        })
    return nav_list

def state_data(zone):
    state_l = []
    for state in zone.states.all():
        state_lgas = state.lgas.all().values('name', 'unique_slug')
        state_l.append({
            'name': state.name,
            'lgas': state_lgas
        })
    return state_l

def country_view(context):
    context.site_title = "Nigeria"
    return render_to_response("ui.html", context_instance=context)

def lga_view(context):
    context.site_title = "LGA View"
    context.lga_id = "'%s'" % context.lga.unique_slug
    return render_to_response("ui.html", context_instance=context)


from utils.csv_reader import CsvReader
import os
from django.conf import settings

def variable_data(request):
    sectors = []
    for sector_table in FacilityTable.objects.all():
        sectors.append(sector_table.display_dict)
    overview_csv = CsvReader(os.path.join(settings.PROJECT_ROOT, "data","table_definitions", "overview.csv"))
    overview_data = []
    for z in overview_csv.iter_dicts():
        overview_data.append(z)
    return HttpResponse(json.dumps({
        'sectors': sectors,
        'overview': overview_data
    }))

def active_districts():
    lgas = LGA.objects.filter(data_loaded=True)
#    lgas = LGA.objects.annotate(facility_count=Count('facilities')).filter(facility_count__gt=0)
    from collections import defaultdict
    states = defaultdict(list)
    for lga in lgas:
        states[lga.state].append(lga)
        
    output = []
    for state, lgas in states.items():
        statelgas = []
        for lga in lgas:
            statelgas.append(
                (lga.name, lga.unique_slug)
                )
        output.append((state.name, statelgas))
    return output

def mustache_template(request, template_name):
    import os
    cur_file = os.path.abspath(__file__)
    cur_dir = os.path.dirname(cur_file)
    template_path = os.path.join(cur_dir, 'mustache', '%s.html' % template_name)
    if not os.path.exists(template_path):
        return HttpResponse('{"ERROR":"No such template: %s"}' % template_name)
    else:
        with open(template_path, 'r') as f:
            return HttpResponse(f.read())

def modes(request, mode_data):
    return render_to_response("modes.html")

def google_help_doc(request):
    google_doc_zip_url = "https://docs.google.com/document/d/1Dze4IZGr0IoIFuFAI_ohKR5mYUt4IAn5Y-uCJmnv1FQ/export?format=zip&id=1Dze4IZGr0IoIFuFAI_ohKR5mYUt4IAn5Y-uCJmnv1FQ&token=AC4w5VhqxjgX9xFvekZGlLQILEIfrl1wSg%3A1312574701000&tfe=yh_186"
    cached_doc_path = os.path.join("docs", "cached_doc.html")
    if not os.path.exists(cached_doc_path):
        import urllib, zipfile
        f = urllib.urlopen(google_doc_zip_url)
        zf_path = "%s.zip" % cached_doc_path
        with open(zf_path, 'w') as foutput:
            foutput.write(f.read())
        z = zipfile.ZipFile(zf_path)
        for name in z.namelist():
            with open(cached_doc_path, 'w') as html_file:
                html_file.write(z.read(name))
    with open(cached_doc_path) as f:
        return HttpResponse(f.read())

