# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Phone'
        db.create_table('odk_dashboard_phone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('most_recent_surveyor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dashboard.Surveyor'], null=True, blank=True)),
            ('most_recent_number', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
        ))
        db.send_create_signal('odk_dashboard', ['Phone'])

        # Adding model 'GPS'
        db.create_table('odk_dashboard_gps', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
            ('altitude', self.gf('django.db.models.fields.FloatField')()),
            ('accuracy', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('odk_dashboard', ['GPS'])

        # Adding model 'SurveyType'
        db.create_table('odk_dashboard_surveytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('odk_dashboard', ['SurveyType'])

        # Adding model 'ParsedSubmission'
        db.create_table('odk_dashboard_parsedsubmission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dropbox.Submission'])),
            ('survey_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dashboard.SurveyType'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('gps', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dashboard.GPS'], null=True, blank=True)),
            ('surveyor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='submissions', null=True, to=orm['odk_dashboard.Surveyor'])),
            ('phone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['odk_dashboard.Phone'])),
        ))
        db.send_create_signal('odk_dashboard', ['ParsedSubmission'])

        # Adding model 'Surveyor'
        db.create_table('odk_dashboard_surveyor', (
            ('user_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('registration', self.gf('django.db.models.fields.related.ForeignKey')(related_name='not_meant_to_be_used', to=orm['odk_dashboard.ParsedSubmission'])),
        ))
        db.send_create_signal('odk_dashboard', ['Surveyor'])


    def backwards(self, orm):
        
        # Deleting model 'Phone'
        db.delete_table('odk_dashboard_phone')

        # Deleting model 'GPS'
        db.delete_table('odk_dashboard_gps')

        # Deleting model 'SurveyType'
        db.delete_table('odk_dashboard_surveytype')

        # Deleting model 'ParsedSubmission'
        db.delete_table('odk_dashboard_parsedsubmission')

        # Deleting model 'Surveyor'
        db.delete_table('odk_dashboard_surveyor')


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
        'odk_dashboard.gps': {
            'Meta': {'object_name': 'GPS'},
            'accuracy': ('django.db.models.fields.FloatField', [], {}),
            'altitude': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {})
        },
        'odk_dashboard.parsedsubmission': {
            'Meta': {'object_name': 'ParsedSubmission'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'gps': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dashboard.GPS']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dashboard.Phone']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dropbox.Submission']"}),
            'survey_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dashboard.SurveyType']"}),
            'surveyor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['odk_dashboard.Surveyor']"})
        },
        'odk_dashboard.phone': {
            'Meta': {'object_name': 'Phone'},
            'device_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'most_recent_number': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'most_recent_surveyor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['odk_dashboard.Surveyor']", 'null': 'True', 'blank': 'True'})
        },
        'odk_dashboard.surveyor': {
            'Meta': {'object_name': 'Surveyor', '_ormbases': ['auth.User']},
            'registration': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'not_meant_to_be_used'", 'to': "orm['odk_dashboard.ParsedSubmission']"}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'odk_dashboard.surveytype': {
            'Meta': {'object_name': 'SurveyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'odk_dropbox.form': {
            'Meta': {'object_name': 'Form'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_string': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'xml_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'odk_dropbox.submission': {
            'Meta': {'object_name': 'Submission'},
            'form': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submissions'", 'null': 'True', 'to': "orm['odk_dropbox.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'xml_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['odk_dashboard']
