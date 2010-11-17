from django.db.models.signals import post_save
from odk_dropbox import utils, models

def add_to_eav(submission):
    handler = utils.parse(submission)
    doc = handler.get_dict()
    keys = doc.keys()
    assert len(keys)==1, "There should be a single root node."
    doc = doc[keys[0]]
    doc["doc_type"] = keys[0]
    doc["form_id_string"] = handler.get_form_id()

    doc["xml"] = submission.xml
    doc["saved"] = submission.saved.isoformat()
    doc["posted"] = submission.posted.isoformat()
    doc["form_id"] = submission.form.id

    # save doc to couchdb, should think more about the doc id
    # for registration the device id should be unique
    # odk_surveys[str(submission.id)] = doc

def _add_to_eav(sender, **kwargs):
    # if this is a new submission add it to the eav
    if kwargs["created"]:
        add_to_eav(kwargs["instance"])

# post_save.connect(_add_to_couch, sender=models.Submission)
