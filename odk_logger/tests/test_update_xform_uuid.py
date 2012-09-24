import os
import csv
from main.tests.test_base import MainTestCase
from odk_logger.models.xform import XForm, DuplicateUUIDError
from odk_logger.management.commands.update_xform_uuids import Command
from utils.model_tools import update_xform_uuid

class TestUpdateXFormUUID(MainTestCase):
    def setUp(self):
        MainTestCase.setUp(self)
        self._publish_transportation_form()
        #
        self.csv_filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "fixtures", "test_update_xform_uuids.csv"
        )
        # get the last defined uuid
        with open(self.csv_filepath, "r") as f:
            lines = csv.reader(f)
            for line in lines:
                self.new_uuid = line[2]

    def test_update_xform_uuid(self):
        c = Command()
        c.handle(file=self.csv_filepath)
        # compare our uuids
        xform = XForm.objects.get(id=self.xform.id)
        self.assertEqual(xform.uuid, self.new_uuid)

    def test_fail_update_on_duplicate_uuid(self):
        self.xform.uuid = self.new_uuid
        self.xform.save()
        try:
            update_xform_uuid(self.user.username, self.xform.id_string,
                self.new_uuid)
        except DuplicateUUIDError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
