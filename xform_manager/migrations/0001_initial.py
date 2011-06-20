# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'XForm'
        db.create_table('xform_manager_xform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('web_title', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('downloadable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('id_string', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('xform_manager', ['XForm'])

        # Adding model 'SurveyType'
        db.create_table('xform_manager_surveytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('xform_manager', ['SurveyType'])

        # Adding model 'Instance'
        db.create_table('xform_manager_instance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('xform', self.gf('django.db.models.fields.related.ForeignKey')(related_name='surveys', to=orm['xform_manager.XForm'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('survey_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['xform_manager.SurveyType'])),
        ))
        db.send_create_signal('xform_manager', ['Instance'])

        # Adding model 'Attachment'
        db.create_table('xform_manager_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['xform_manager.Instance'])),
            ('media_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('xform_manager', ['Attachment'])


    def backwards(self, orm):
        
        # Deleting model 'XForm'
        db.delete_table('xform_manager_xform')

        # Deleting model 'SurveyType'
        db.delete_table('xform_manager_surveytype')

        # Deleting model 'Instance'
        db.delete_table('xform_manager_instance')

        # Deleting model 'Attachment'
        db.delete_table('xform_manager_attachment')


    models = {
        'xform_manager.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['xform_manager.Instance']"}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'xform_manager.instance': {
            'Meta': {'object_name': 'Instance'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'survey_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['xform_manager.SurveyType']"}),
            'xform': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'surveys'", 'to': "orm['xform_manager.XForm']"}),
            'xml': ('django.db.models.fields.TextField', [], {})
        },
        'xform_manager.surveytype': {
            'Meta': {'object_name': 'SurveyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'xform_manager.xform': {
            'Meta': {'ordering': "('id_string',)", 'object_name': 'XForm'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'downloadable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_string': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'web_title': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'xml': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['xform_manager']
