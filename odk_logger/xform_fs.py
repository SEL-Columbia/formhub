import os
import glob
import re

class XFormInstanceFS(object):
    def __init__(self, filepath):
        self.path = filepath
        self.directory, self.filename = os.path.split(self.path)
        self.xform_id = re.sub(".xml", "", self.filename)

    @property
    def photos(self):
        if not hasattr(self, '_photos'):
            available_photos = glob.glob(os.path.join(self.directory, "*.jpg"))
            self._photos = []
            for photo_path in available_photos:
                _pdir, photo = os.path.split(photo_path)
                if self.xml.find(photo) > 0:
                    self._photos.append(photo_path)
        return self._photos

    @property
    def metadata_directory(self):
        if not hasattr(self, '_metadata_directory'):
            instances_dir = os.path.join(self.directory, "..", "..", "instances")
            metadata_directory = os.path.join(self.directory, "..", "..", "metadata")
            if os.path.exists(instances_dir) and os.path.exists(metadata_directory):
                self._metadata_directory = os.path.abspath(metadata_directory)
            else:
                self._metadata_directory = False
        return self._metadata_directory

    def metadata_instance_file(self, collect_version):
        if collect_version == "1.1.5":
            return os.path.join(self.metadata_directory, "data")
        elif collect_version == "1.1.7":
            return os.path.join(self.metadata_directory, "instances.db")
        else:
            return None

    @property
    def xml(self):
        if not hasattr(self, '_xml'):
            with open(self.path, 'r') as f:
                self._xml = f.read()
        return self._xml

    @classmethod
    def is_valid_odk_instance(cls, filepath):
        if not filepath.endswith(".xml"):
            return False
        with open(filepath, 'r') as ff:
            fxml = ff.read()
            if fxml.find("""<?xml version='1.0' ?>""") == 0:
                return True
        return False

    @property
    def instance_file_path(self):
        try:
            return "/sdcard/odk/instances/%s" % self.path.split("odk/instances/")[1]
        except Exception, e:
            return None

    @property
    def instance_status(self):
        """
        I probably have access to the metadata directory here:
          `self.metadata_directory`
        and i need to know the status.

        use sqlalchemy to open the database and retrieve the status
        of this form.

        see import_tools.py to find how it was done in odk collect 1.1.5
        """
        collect_version = self._odk_collect_version
        assert collect_version in ["1.1.5", "1.1.7", None]
        
        path_to_metadata_file = self.metadata_instance_file(collect_version)
        instance_file_path = self.instance_file_path

        # for 1.1.7 (at least)
        # read file: "path_to_metadata_file"
        # find the row where instanceFilePath == "instance_file_path"
        # return the status

        return "i_can_not_haz_status"

    @property
    def _odk_collect_version(self):
        if self.metadata_directory:
            md = self.metadata_directory
            if os.path.exists(os.path.join(md, "forms.db")):
                return "1.1.7"
            elif os.path.exists(os.path.join(md, "data")):
                return "1.1.5"
        return None

    def __str__(self):
        return "<XForm XML: %s>" % self.xform_id
