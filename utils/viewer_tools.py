import os
import traceback
import requests
import zipfile

from xml.dom import minidom
from tempfile import NamedTemporaryFile
from urlparse import urljoin

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.core.files.storage import get_storage_class

import common_tags as tag


SLASH = u"/"


class MyError(Exception):
    pass


def image_urls_for_form(xform):
    return sum([
        image_urls(s) for s in xform.surveys.all()
    ], [])


def get_path(path, suffix):
    fileName, fileExtension = os.path.splitext(path)
    return fileName + suffix + fileExtension


def image_urls(instance):
    default_storage = get_storage_class()()
    urls = []
    suffix = settings.THUMB_CONF['medium']['suffix']
    for a in instance.attachments.all():
        if default_storage.exists(get_path(a.media_file.name, suffix)):
            url = default_storage.url(
                get_path(a.media_file.name, suffix))
        else:
            url = a.media_file.url
        urls.append(url)
    return urls


def parse_xform_instance(xml_str):
    """
    'xml_str' is a str object holding the XML of an XForm
    instance. Return a python object representation of this XML file.
    """
    xml_obj = minidom.parseString(xml_str)
    root_node = xml_obj.documentElement
    # go through the xml object creating a corresponding python object
    # NOTE: THIS WILL DESTROY ANY DATA COLLECTED WITH REPEATABLE NODES
    # THIS IS OKAY FOR OUR USE CASE, BUT OTHER USERS SHOULD BEWARE.
    survey_data = dict(_path_value_pairs(root_node))
    assert len(list(_all_attributes(root_node))) == 1, \
        _(u"There should be exactly one attribute in this document.")
    survey_data.update({
        tag.XFORM_ID_STRING: root_node.getAttribute(u"id"),
        tag.INSTANCE_DOC_NAME: root_node.nodeName,
    })
    return survey_data


def _path(node):
    n = node
    levels = []
    while n.nodeType != n.DOCUMENT_NODE:
        levels = [n.nodeName] + levels
        n = n.parentNode
    return SLASH.join(levels[1:])


def _path_value_pairs(node):
    """
    Using a depth first traversal of the xml nodes build up a python
    object in parent that holds the tree structure of the data.
    """
    if len(node.childNodes) == 0:
        # there's no data for this leaf node
        yield _path(node), None
    elif len(node.childNodes) == 1 and \
            node.childNodes[0].nodeType == node.TEXT_NODE:
        # there is data for this leaf node
        yield _path(node), node.childNodes[0].nodeValue
    else:
        # this is an internal node
        for child in node.childNodes:
            for pair in _path_value_pairs(child):
                yield pair


def _all_attributes(node):
    """
    Go through an XML document returning all the attributes we see.
    """
    if hasattr(node, "hasAttributes") and node.hasAttributes():
        for key in node.attributes.keys():
            yield key, node.getAttribute(key)
    for child in node.childNodes:
        for pair in _all_attributes(child):
            yield pair


def report_exception(subject, info, exc_info=None):
    if exc_info:
        cls, err = exc_info[:2]
        info += _(u"Exception in request: %(class)s: %(error)s") \
            % {'class': cls.__name__, 'error': err}
        info += u"".join(traceback.format_exception(*exc_info))

    if settings.DEBUG:
        print subject
        print info
    else:
        mail_admins(subject=subject, message=info)


def django_file(path, field_name, content_type):
    # adapted from here:
    # http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None
    )


def export_def_from_filename(filename):
    from odk_viewer.models.export import Export
    path, ext = os.path.splitext(filename)
    ext = ext[1:]
    # try get the def from extension
    mime_type = Export.EXPORT_MIMES[ext]
    return ext, mime_type


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def enketo_url(form_url, id_string, instance_xml=None,
               instance_id=None, return_url=None):
    if not hasattr(settings, 'ENKETO_URL')\
            and not hasattr(settings, 'ENKETO_API_SURVEY_PATH'):
        return False

    url = urljoin(settings.ENKETO_URL, settings.ENKETO_API_SURVEY_PATH)

    values = {
        'form_id': id_string,
        'server_url': form_url
    }
    if instance_id is not None and instance_xml is not None:
        url = urljoin(settings.ENKETO_URL, settings.ENKETO_API_INSTANCE_PATH)
        values.update({
            'instance': instance_xml,
            'instance_id': instance_id,
            'return_url': return_url
        })
    req = requests.post(url, data=values,
                        auth=(settings.ENKETO_API_TOKEN, ''), verify=False)
    if req.status_code in [200, 201]:
        try:
            response = req.json()
        except ValueError:
            pass
        else:
            if 'edit_url' in response:
                return response['edit_url']
            if 'url' in response:
                return response['url']
    else:
        try:
            response = req.json()
        except ValueError:
            pass
        else:
            if 'message' in response:
                raise Exception(response['message'])
    return False


def create_attachments_zipfile(attachments):
    # create zip_file
    tmp = NamedTemporaryFile(delete=False)
    z = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    for attachment in attachments:
        default_storage = get_storage_class()()
        if default_storage.exists(attachment.media_file.name):
            try:
                z.write(attachment.full_filepath, attachment.media_file.name)
            except Exception, e:
                report_exception("Create attachment zip exception", e)
    z.close()
    return tmp.name
