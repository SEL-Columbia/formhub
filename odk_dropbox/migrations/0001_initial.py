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
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('id_string', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('odk_dropbox', ['Form'])

        # Adding model 'Instance'
        db.create_table('odk_dropbox_instance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='instances', null=True, to=orm['odk_dropbox.Form'])),
            ('hash', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('odk_dropbox', ['Instance'])

        # Adding model 'InstanceImage'
        db.create_table('odk_dropbox_instanceimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['odk_dropbox.Instance'])),
            ('image', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('odk_dropbox', ['InstanceImage'])

        # Adding model 'Submission'
        db.create_table('odk_dropbox_submission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('instance', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['odk_dropbox.Instance'])),
        ))
        db.send_create_signal('odk_dropbox', ['Submission'])


    def backwards(self, orm):
        
        # Deleting model 'Form'
        db.delete_table('odk_dropbox_form')

        # Deleting model 'Instance'
        db.delete_table('odk_dropbox_instance')

        # Deleting model 'InstanceImage'
        db.delete_table('odk_dropbox_instanceimage')

        # Deleting model 'Submission'
        db.delete_table('odk_dropbox_submission')


    models = {
        'odk_dropbox.form': {
            'Meta': {'ordering': "('id_string',)", 'object_name': 'Form'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_string': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'xml_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'odk_dropbox.instance': {
            'Meta': {'object_name': 'Instance'},
            'form': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'instances'", 'null': 'True', 'to': "orm['odk_dropbox.Form']"}),
            'hash': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'xml_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'odk_dropbox.instanceimage': {
            'Meta': {'object_name': 'InstanceImage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['odk_dropbox.Instance']"})
        },
        'odk_dropbox.submission': {
            'Meta': {'ordering': "('posted',)", 'object_name': 'Submission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['odk_dropbox.Instance']"}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['odk_dropbox']
