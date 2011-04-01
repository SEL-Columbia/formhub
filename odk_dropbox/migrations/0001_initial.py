# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Form'
        db.create_table('odk_dropbox_form', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('id_string', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('odk_dropbox', ['Form'])

        # Adding model 'Submission'
        db.create_table('odk_dropbox_submission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='submissions', null=True, to=orm['odk_dropbox.Form'])),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('odk_dropbox', ['Submission'])

        # Adding model 'SubmissionImage'
        db.create_table('odk_dropbox_submissionimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('submission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['odk_dropbox.Submission'])),
            ('image', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('odk_dropbox', ['SubmissionImage'])


    def backwards(self, orm):
        
        # Deleting model 'Form'
        db.delete_table('odk_dropbox_form')

        # Deleting model 'Submission'
        db.delete_table('odk_dropbox_submission')

        # Deleting model 'SubmissionImage'
        db.delete_table('odk_dropbox_submissionimage')


    models = {
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
        },
        'odk_dropbox.submissionimage': {
            'Meta': {'object_name': 'SubmissionImage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['odk_dropbox.Submission']"})
        }
    }

    complete_apps = ['odk_dropbox']
