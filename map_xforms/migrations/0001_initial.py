# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SurveyTypeMapData'
        db.create_table('map_xforms_surveytypemapdata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('survey_type', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['xform_manager.SurveyType'], unique=True)),
            ('color', self.gf('django.db.models.fields.CharField')(default='Black', max_length=12)),
        ))
        db.send_create_signal('map_xforms', ['SurveyTypeMapData'])
        
        from map_xforms.models import SurveyTypeMapData
        from xform_manager.models import SurveyType
        survey_types = SurveyType.objects.all()
        for st in survey_types:
            survey_color = 'Black'
            if st.slug=='water':
                survey_color = 'Blue'
            elif st.slug=='school':
                survey_color = 'Green'
            elif st.slug=='health':
                survey_color = 'Red'
            tt = SurveyTypeMapData(survey_type=st, color=survey_color)
            tt.save()

    def backwards(self, orm):
        
        # Deleting model 'SurveyTypeMapData'
        db.delete_table('map_xforms_surveytypemapdata')


    models = {
        'map_xforms.surveytypemapdata': {
            'Meta': {'object_name': 'SurveyTypeMapData'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'Black'", 'max_length': '12'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'survey_type': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['xform_manager.SurveyType']", 'unique': 'True'})
        },
        'xform_manager.surveytype': {
            'Meta': {'object_name': 'SurveyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['map_xforms']
