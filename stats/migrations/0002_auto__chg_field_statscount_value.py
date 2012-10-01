# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'StatsCount.value'
        db.alter_column('stats_statscount', 'value', self.gf('django.db.models.fields.IntegerField')())


    def backwards(self, orm):
        
        # Changing field 'StatsCount.value'
        db.alter_column('stats_statscount', 'value', self.gf('django.db.models.fields.SmallIntegerField')())


    models = {
        'stats.statscount': {
            'Meta': {'object_name': 'StatsCount'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['stats']
