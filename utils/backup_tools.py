import codecs
from datetime import datetime
import errno
import os
import shutil
import sys
import tempfile
import zipfile
from time import sleep

from onadata.apps.logger.import_tools import django_file
from onadata.apps.logger.models import Instance
from onadata.libs.utils.logger_tools import create_instance
from onadata.libs.utils.model_tools import queryset_iterator


DATE_FORMAT = "%Y-%m-%d-%H-%M-%S"


def _date_created_from_filename(filename):
    base_name, ext = os.path.splitext(filename)
    parts = base_name.split("-")
    if len(parts) < 6:
        raise ValueError(
            "Inavlid filename - it must be in the form"
            " 'YYYY-MM-DD-HH-MM-SS[-i].xml'")
    parts_dict = dict(
        zip(["year", "month", "day", "hour", "min", "sec"], parts))
    return datetime.strptime(
        "%(year)s-%(month)s-%(day)s-%(hour)s-%(min)s-%(sec)s" %
        parts_dict, DATE_FORMAT)


def create_zip_backup(zip_output_file, user, xform=None):
    # create a temp dir that we'll create our structure within and zip it
    # when we are done
    tmp_dir_path = tempfile.mkdtemp()

    instances_path = os.path.join(tmp_dir_path, "instances")

    # get the xls file from storage

    # for each submission in the database - create an xml file in this
    # form
    # /<id_string>/YYYY/MM/DD/YYYY-MM-DD-HH-MM-SS.xml
    qs = Instance.objects.filter(xform__user=user)
    if xform:
        qs = qs.filter(xform=xform)

    num_instances = qs.count()
    done = 0
    sys.stdout.write("Creating XML Instances\n")
    for instance in queryset_iterator(qs, 100):
        # get submission time
        date_time_str = instance.date_created.strftime(DATE_FORMAT)
        date_parts = date_time_str.split("-")
        sub_dirs = os.path.join(*date_parts[:3])
        # create the directories
        full_path = os.path.join(instances_path, sub_dirs)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        full_xml_path = os.path.join(full_path, date_time_str + ".xml")
        # check for duplicate file names
        file_index = 1
        while os.path.exists(full_xml_path):
            full_xml_path = os.path.join(
                full_path, "%s-%d.xml" % (date_time_str, file_index))
            file_index += 1
        # create the instance xml
        with codecs.open(full_xml_path, "wb", "utf-8") as f:
            f.write(instance.xml)
        done += 1
        sys.stdout.write("\r%.2f %% done" % (
            float(done)/float(num_instances) * 100))
        sys.stdout.flush()
        sleep(0)

    # write zip file
    sys.stdout.write("\nWriting to ZIP arhive.\n")
    zf = zipfile.ZipFile(zip_output_file, "w")
    done = 0
    for dir_path, dir_names, file_names in os.walk(tmp_dir_path):
        for file_name in file_names:
            archive_path = dir_path.replace(tmp_dir_path + os.path.sep,
                                            "", 1)
            zf.write(os.path.join(dir_path, file_name),
                     os.path.join(archive_path, file_name))
            done += 1
            sys.stdout.write("\r%.2f %% done" % (
                float(done)/float(num_instances) * 100))
            sys.stdout.flush()
            sleep(0)
    zf.close()
    # removed dir tree
    shutil.rmtree(tmp_dir_path)
    sys.stdout.write("\nBackup saved to %s\n" % zip_output_file)


def restore_backup_from_zip(zip_file_path, username):
    try:
        temp_directory = tempfile.mkdtemp()
        zf = zipfile.ZipFile(zip_file_path)

        zf.extractall(temp_directory)
    except zipfile.BadZipfile:
        sys.stderr.write("Bad zip arhcive.")
    else:
        return restore_backup_from_path(temp_directory, username, "backup")
    finally:
        shutil.rmtree(temp_directory)


def restore_backup_from_xml_file(xml_instance_path, username):
    # check if its a valid xml instance
    file_name = os.path.basename(xml_instance_path)
    xml_file = django_file(
        xml_instance_path,
        field_name="xml_file",
        content_type="text/xml")
    media_files = []
    try:
        date_created = _date_created_from_filename(file_name)
    except ValueError as e:
        sys.stderr.write(
            "Couldn't determine date created from filename: '%s'\n" %
            file_name)
        date_created = datetime.now()

    sys.stdout.write("Creating instance from '%s'\n" % file_name)
    try:
        create_instance(
            username, xml_file, media_files,
            date_created_override=date_created)
        return 1
    except Exception as e:
        sys.stderr.write(
            "Could not restore %s, create instance said: %s\n" %
            (file_name, e))
        return 0


def restore_backup_from_path(dir_path, username, status):
    """
    Only restores xml submissions, media files are assumed to still be in
    storage and will be retrieved by the filename stored within the submission
    """
    num_instances = 0
    num_restored = 0
    for dir_path, dir_names, file_names in os.walk(dir_path):
        for file_name in file_names:
            # check if its a valid xml instance
            xml_instance_path = os.path.join(dir_path, file_name)
            num_instances += 1
            num_restored += restore_backup_from_xml_file(
                xml_instance_path,
                username)
    return num_instances, num_restored
