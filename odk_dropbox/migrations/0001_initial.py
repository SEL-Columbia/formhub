# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'District'
        db.create_table('odk_dropbox_district', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('depth', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('numchild', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('kml_present', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('latlng_string', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('odk_dropbox', ['District'])

        # Adding model 'XForm'
        db.create_table('odk_dropbox_xform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('id_string', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('odk_dropbox', ['XForm'])

        # Adding model 'Phone'
        db.create_table('odk_dropbox_phone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
        ))
        db.send_create_signal('odk_dropbox', ['Phone'])

        # Adding model 'Surveyor'
        db.create_table('odk_dropbox_surveyor', (
            ('user_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('odk_dropbox', ['Surveyor'])

        # Adding model 'SurveyType'
        db.create_table('odk_dropbox_surveytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('odk_dropbox', ['SurveyType'])

        # Adding model 'Instance'
        db.create_table('odk_dropbox_instance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('xform', self.gf('django.db.models.fields.related.ForeignKey')(related_name='surveys', to=orm['odk_dropbox.XForm'])),
            ('phone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dropbox.Phone'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('surveyor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dropbox.Surveyor'], null=True)),
            ('district', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dropbox.District'], null=True)),
            ('survey_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dropbox.SurveyType'])),
        ))
        db.send_create_signal('odk_dropbox', ['Instance'])

        # Adding model 'Attachment'
        db.create_table('odk_dropbox_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['odk_dropbox.Instance'])),
            ('attachment', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('odk_dropbox', ['Attachment'])


    def backwards(self, orm):
        
        # Deleting model 'District'
        db.delete_table('odk_dropbox_district')

        # Deleting model 'XForm'
        db.delete_table('odk_dropbox_xform')

        # Deleting model 'Phone'
        db.delete_table('odk_dropbox_phone')

        # Deleting model 'Surveyor'
        db.delete_table('odk_dropbox_surveyor')

        # Deleting model 'SurveyType'
        db.delete_table('odk_dropbox_surveytype')

        # Deleting model 'Instance'
        db.delete_table('odk_dropbox_instance')

        # Deleting model 'Attachment'
        db.delete_table('odk_dropbox_attachment')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'odk_dropbox.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['odk_dropbox.Instance']"})
        },
        'odk_dropbox.district': {
            'Meta': {'object_name': 'District'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kml_present': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latlng_string': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'odk_dropbox.instance': {
            'Meta': {'object_name': 'Instance'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dropbox.District']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dropbox.Phone']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'survey_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dropbox.SurveyType']"}),
            'surveyor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dropbox.Surveyor']", 'null': 'True'}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'surveys'", 'to': "orm['odk_dropbox.XForm']"}),
            'xml': ('django.db.models.fields.TextField', [], {})
        },
        'odk_dropbox.phone': {
            'Meta': {'object_name': 'Phone'},
            'device_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'odk_dropbox.surveyor': {
            'Meta': {'object_name': 'Surveyor', '_ormbases': ['auth.User']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'odk_dropbox.surveytype': {
            'Meta': {'object_name': 'SurveyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'odk_dropbox.xform': {
            'Meta': {'ordering': "('id_string',)", 'object_name': 'XForm'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_string': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'xml': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['odk_dropbox']
