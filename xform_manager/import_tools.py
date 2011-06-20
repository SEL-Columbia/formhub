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

def import_instance(path_to_instance_folder, status):
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
    # db.
    models.get_or_create_instance(xml_file, images, status)

    # close the files
    xml_file.close()
    for i in images: i.close()

def import_instances_from_phone(path_to_odk_folder):
    print '.'
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
        regexp = r"^/mnt/sdcard/odk/instances/([^/]+)/[^/]+.xml$"
        for instance in instances:
            m = re.search(regexp, instance[u'path'])
            assert m
            instance_folder_name = m.group(1)
            instance[u'path_to_instance_folder'] = os.path.join(
                path_to_odk_folder, u'instances',
                instance_folder_name
                )

    add_path_to_instance_folder()
    for i in instances:
        try:
            import_instance(i[u'path_to_instance_folder'], i[u'status'])
        except Exception as e:
            print e


def import_instances_from_jonathan(containing_folder):
    phone_folders = glob.glob( os.path.join(containing_folder, "*") )
    for phone_folder in phone_folders:
        odk_folder = os.path.join(phone_folder, 'odk')
        import_instances_from_phone(odk_folder)


# this script is intended to be called as follows

## python manage.py shell
## from xform_manager.import_tools import import_instances_from_jonathan
## import_instances_from_jonathan("Baseline Phone Data/")

# two folders with interesting notes, will break this script
# rm -r 137/
# rm -r 148\ duplicated/
