
from south.db import db
from south.v2 import SchemaMigration

class Migration(SchemaMigration):
    """Add an index to the uuid columns in both the odk_logger_xform and
    odk_logger_instance tables"""

    def forwards(self, orm):
        db.execute("create index odk_logger_xform_uuid_idx on odk_logger_xform (uuid)")
        db.execute("create index odk_logger_instance_uuid_idx on odk_logger_instance (uuid)")

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.") 
