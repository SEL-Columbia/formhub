from django_mongokit import get_database
db = get_database()
xform_instances = db.instances

from django.db import models
from xform import XForm
from .. import utils, tag

class Instance(models.Model):
    xml = models.TextField()
    xform = models.ForeignKey(XForm, related_name="instances")

    class Meta:
        app_label = 'odk_dropbox'

    def _link(self):
        """Link this instance with its corresponding form."""
        data = utils.parse_xform_instance(self.xml)
        self.xform = XForm.objects.get(id_string=data[tag.FORM_ID])

    def _sync_mongo(self):
        data = utils.parse_xform_instance(self.xml)
        self.xform.clean_instance(data)
        data["_id"] = self.id
        xform_instances.save(data)

    def save(self, *args, **kwargs):
        self._link()
        super(Instance, self).save(*args, **kwargs)
        self._sync_mongo()

class Attachment(models.Model):
    instance = models.ForeignKey(Instance, related_name="attachments")
    attachment = models.FileField(upload_to="attachments")

    class Meta:
        app_label = 'odk_dropbox'

def get_or_create_instance(xml_file, media_files):
    """
    I used to check if this file had been submitted already, I've
    taken this out because it was too slow. Now we're going to create
    a way for an admin to mark duplicate instances. This should
    simplify things a bit.
    """
    xml_file.open()
    xml = xml_file.read()
    xml_file.close()

    try:
        instance, created = Instance.objects.get_or_create(xml=xml)
        if created:
            for f in media_files:
                Attachment.objects.create(instance=instance, attachment=f)
        return instance, created
    except XForm.DoesNotExist:
        utils.report_exception("Missing XForm", "TRY TO GET ID HERE")
        

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
