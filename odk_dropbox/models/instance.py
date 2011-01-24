from django_mongokit import get_database
db = get_database()

xform_instances = db.instances
from .. import utils, tag
from xform import XForm

def make_instance(xml_file, media_files):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate submissions. This should
    simplify things a bit.
    """
    data = utils.parse_xform_instance(xml_file)

    try:
        xform = XForm.objects.get(id_string=data[tag.FORM_ID])
    except XForm.DoesNotExist:
        utils.report_exception("missing form", data[tag.FORM_ID])
        return None

    xform.clean_instance(data)

    doc_id = xform_instances.insert(data)
    print doc_id

    # attach all the files
    # for f in [xml_file] + media_files: doc.put_attachment(f)


# def parse(instance):
#     handler = utils.parse_instance(instance)
#     d = handler.get_dict()

#     for k in ["start", "end", "device_id"]:
#         if k not in d:
#             raise Exception("Required field missing" , k)

#     # create parsed instance object
#     kwargs = {"instance" : instance}

#     m = re.search(r"^([a-zA-Z]+)", handler.get_form_id())
#     survey_type_name = m.group(1).lower()
#     survey_type, created = \
#         SurveyType.objects.get_or_create(name=survey_type_name)
#     kwargs["survey_type"] = survey_type

#     for key in ["start", "end"]:
#         s = d[key]
#         kwargs[key] = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
#         if not starts_with(kwargs[key].isoformat(), s):
#             utils.report_exception(
#                 "datetime object doesn't recreate original string",
#                 "orginal: %(original)s datetime object: %(parsed)s" %
#                 {"original" : s, "parsed" : kwargs[key].isoformat()}
#                 )
#     kwargs["date"] = kwargs["end"].date()

#     lga = matching_key(d, r"^lga\d*$")
#     if lga:
#         gps_str = d.get("geopoint","")
#         gps = None
#         if gps_str:
#             values = gps_str.split(" ")
#             keys = ["latitude", "longitude", "altitude", "accuracy"]
#             items = zip(keys, values)
#             gps, created = GPS.objects.get_or_create(**dict(items))
#         location, created = Location.objects.get_or_create(
#             name=d[lga], gps=gps
#             )
#         kwargs["location"] = location

#     phone, created = \
#         Phone.objects.get_or_create(device_id=d["device_id"])
#     kwargs["phone"] = phone

#     ps = ParsedInstance.objects.create(**kwargs)

#     if ps.survey_type.name=="registration":
#         names = d["name"].split()
#         kwargs = {"username" : str(Surveyor.objects.all().count()),
#                   "password" : "none",
#                   "last_name" : names.pop(),
#                   "first_name" : " ".join(names),
#                   "registration" : ps}
#         surveyor = Surveyor.objects.create(**kwargs)
#         phone.most_recent_surveyor = surveyor
#         phone.save()
#     ps.save()

# def _parse(sender, **kwargs):
#     # make sure we haven't parsed this instance before
#     qs = ParsedInstance.objects.filter(instance=kwargs["instance"])
#     if qs.count()==0:
#         try:
#             parse(kwargs["instance"])
#         except:
#             # catch any exceptions and print them to the error log
#             # it'd be good to add more info to these error logs
#             e = sys.exc_info()[1]
#             utils.report_exception(
#                 "problem parsing instance",
#                 e.__unicode__(),
#                 sys.exc_info()
#                 )

# post_save.connect(_parse, sender=Instance)
