# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import glob, os, re, sys
from sqlalchemy import create_engine, MetaData, Table
from django.core.files.uploadedfile import InMemoryUploadedFile
import models

# odk
# ├── forms
# │   ├── Agriculture_2011_03_18.xml
# │   ├── Education_2011_03_18.xml
# │   ├── Health_2011_03_18.xml
# │   ├── LGA_2011_03_18.xml
# │   ├── Registration_2011_03_18.xml
# │   └── Water_2011_03_18.xml
# ├── instances
# │   ├── Education_2011_03_18_2011-03-23_11-07-36
# │   │   ├── 1300878537573.jpg
# │   │   └── Education_2011_03_18_2011-03-23_11-07-36.xml
# │   ├── Registration_2011_03_18_2011-03-21_19-33-34
# │   │   └── Registration_2011_03_18_2011-03-21_19-33-34.xml
# └── metadata
#     └── data

def django_file(path, field_name, content_type):
    # adapted from here: http://groups.google.com/group/django-users/browse_thread/thread/834f988876ff3c45/
    f = open(path)
    return InMemoryUploadedFile(
        file=f,
        field_name=field_name,
        name=f.name,
        content_type=content_type,
        size=os.path.getsize(path),
        charset=None
        )

def import_instance(path_to_instance_folder, status, user):
    xml_files = glob.glob( os.path.join(path_to_instance_folder, "*.xml") )
    if len(xml_files)<1: return
    if len(xml_files)>1: raise Exception("Too many XML files.")
    xml_file = django_file(xml_files[0],
                           field_name="xml_file",
                           content_type="text/xml")
    images = []
    for jpg in glob.glob(os.path.join(path_to_instance_folder, "*.jpg")):
        image_file = django_file(jpg,
                                 field_name="image",
                                 content_type="image/jpeg")
        images.append(image_file)
    # todo: if an instance has been submitted make sure all the
    # files are in the database.
    # there shouldn't be any instances with a submitted status in the
    instance = models.create_instance(user.username, xml_file, images, status) 
    # close the files
    xml_file.close()
    for i in images: i.close()
    return instance

def import_instances_from_phone(path_to_odk_folder, user):
    path_to_sqlite_db = os.path.join(path_to_odk_folder,
                                     'metadata', 'data')
    def get_table_describing_odk_files():
        db = create_engine('sqlite:///%s' % path_to_sqlite_db)
        metadata = MetaData()
        metadata.bind = db
        return Table('files', metadata, autoload=True)

    files = get_table_describing_odk_files()
    column_names = [c.name for c in files.columns]

    def get_list_of_odk_instances():
        result = []
        for row in files.select().execute().fetchall():
            d = dict(zip(column_names, row))
            # todo: figure out how to do where statements
            if d[u'type'] == u'instance':
                result.append(d)
        return result

    instances = get_list_of_odk_instances()

    def add_path_to_instance_folder():
        regexp = r"/sdcard/odk/instances/([^/]+)/[^/]+.xml$"
        for instance in instances:
            m = re.search(regexp, instance[u'path'])
            assert m, str(instance)
            instance_folder_name = m.group(1)
            instance[u'path_to_instance_folder'] = os.path.join(
                path_to_odk_folder, u'instances',
                instance_folder_name
                )

    add_path_to_instance_folder()
    count = 0
    for i in instances:
        try:
            instance = import_instance(i[u'path_to_instance_folder'], i[u'status'], user)
            if instance: count += 1
        except Exception as e:
            print e
    return count

import zipfile
import tempfile
import shutil
from odk_logger.xform_fs import XFormInstanceFS

def iterate_through_odk_instances(dirpath, callback):
    count = 0
    errors = 0
    for directory, subdirs, subfiles in os.walk(dirpath):
        for filename in subfiles:
            filepath = os.path.join(directory, filename)
            if XFormInstanceFS.is_valid_odk_instance(filepath):
                xfxs = XFormInstanceFS(filepath)
                try:
                    count += callback(xfxs)
                except:
                    errors += 1
                del(xfxs)
    return (count, errors)

def import_instances_from_zip(zipfile_path, user, default_status="zip_unspecified"):
    count = 0
    try:
        temp_directory = tempfile.mkdtemp()
        zf = zipfile.ZipFile(zipfile_path)
        zf.extractall(temp_directory)
        def callback(xform_fs):
            """
            This callback is passed an instance of a XFormInstanceFS.
            See xform_fs.py for more info.
            """
            xml_file = django_file(xform_fs.path,
                                   field_name="xml_file",
                                   content_type="text/xml")
            images = [django_file(jpg, field_name="image",
                            content_type="image/jpeg") for jpg in xform_fs.photos]

            submission_status = xform_fs.instance_status

            if not submission_status:
                submission_status = default_status
            # todo: if an instance has been submitted make sure all the
            # files are in the database.
            # there shouldn't be any instances with a submitted status in the
            instance = models.create_instance(user.username, xml_file, images, submission_status)
            # close the files
            xml_file.close()
            for i in images: i.close()
            if instance:
                return 1
            else:
                return 0
        count, errors = iterate_through_odk_instances(temp_directory, callback)
    finally:
        shutil.rmtree(temp_directory)
    return count

# this script is intended to be called as follows

## python manage.py shell
## from odk_logger.import_tools import import_instances_from_jonathan
## import_instances_from_jonathan("Baseline Phone Data/")

# two folders with interesting notes, will break this script
# rm -r 137/
# rm -r 148\ duplicated/
