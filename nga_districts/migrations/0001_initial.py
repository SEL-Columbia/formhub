# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Zone'
        db.create_table('nga_districts_zone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('nga_districts', ['Zone'])

        # Adding model 'State'
        db.create_table('nga_districts_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('zone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='states', to=orm['nga_districts.Zone'])),
        ))
        db.send_create_signal('nga_districts', ['State'])

        # Adding model 'LGA'
        db.create_table('nga_districts_lga', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='lgas', to=orm['nga_districts.State'])),
            ('scale_up', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('unique_slug', self.gf('django.db.models.fields.TextField')(null=True)),
            ('afr_id', self.gf('django.db.models.fields.TextField')(null=True)),
            ('kml_id', self.gf('django.db.models.fields.TextField')(null=True)),
            ('latlng_str', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('nga_districts', ['LGA'])


    def backwards(self, orm):
        
        # Deleting model 'Zone'
        db.delete_table('nga_districts_zone')

        # Deleting model 'State'
        db.delete_table('nga_districts_state')

        # Deleting model 'LGA'
        db.delete_table('nga_districts_lga')


    models = {
        'nga_districts.lga': {
            'Meta': {'object_name': 'LGA'},
            'afr_id': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kml_id': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'latlng_str': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'scale_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lgas'", 'to': "orm['nga_districts.State']"}),
            'unique_slug': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'nga_districts.state': {
            'Meta': {'object_name': 'State'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'states'", 'to': "orm['nga_districts.Zone']"})
        },
        'nga_districts.zone': {
            'Meta': {'object_name': 'Zone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['nga_districts']
